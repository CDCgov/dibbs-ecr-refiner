import io
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.demo import XML_FILE_ERROR, ZIP_READING_ERROR
from app.api.validation.file_validation import validate_zip_file
from app.core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from app.db.conditions.db import get_condition_by_id_db, get_included_conditions_db
from app.db.configurations.db import get_configuration_by_id_db
from app.db.demo.model import Condition
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.aws.s3 import upload_refined_ecr
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import (
    create_refined_ecr_zip_in_memory,
    create_split_condition_filename,
    read_xml_zip,
)
from app.services.format import normalize_xml, strip_comments
from app.services.logger import get_logger
from app.services.sample_file import create_sample_zip_file, get_sample_zip_path
from app.services.testing import inline_testing
from app.services.xslt import get_path_to_xslt_stylesheet, transform_xml_to_html

from .models import ConfigurationTestResponse

router = APIRouter(prefix="/test")


def _upload_to_s3():
    """
    Returns a function to upload an eICR/RR pair .zip to S3.
    """
    return upload_refined_ecr


@router.post(
    "",
    response_model=ConfigurationTestResponse,
    tags=["configurations"],
    operation_id="runInlineConfigurationTest",
)
async def run_configuration_test(
    id: UUID = Form(...),
    uploaded_file: UploadFile | None = File(None),
    create_output_zip: Callable[..., tuple[str, io.BytesIO]] = Depends(
        lambda: create_refined_ecr_zip_in_memory
    ),
    upload_refined_files_to_s3: Callable[
        [UUID, str, io.BytesIO, str, Logger], str
    ] = Depends(_upload_to_s3),
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
    sample_zip_path: Path = Depends(get_sample_zip_path),
    logger: Logger = Depends(get_logger),
) -> ConfigurationTestResponse:
    """
    Runs an inline test of a given configuration against an eICR/RR pair.

    This endpoint orchestrates the validation and refinement process by:
    1. Handling file input, either from a user upload or a default sample file.
    2. Calling the `inline_testing` service, which validates that the specified
       configuration's condition is reportable in the provided file.
    3. Handling the service response:
        - If validation fails, raises a 400 Bad Request with a specific error.
        - If successful, proceeds with the returned refined document.
    4. Packaging the original eICR, RR, and the single refined eICR into a
       new in-memory zip archive.
    5. Uploading the archive to S3 and generating a pre-signed download URL.
    6. Returning a `ConfigurationTestResponse` with the download URL and details
       of the successful refinement.

    Args:
        id: The ID of the configuration to test.
        uploaded_file: An optional user-provided zip file with an eICR and RR.
        create_output_zip: Dependency to create a zip archive in memory.
        upload_refined_files_to_s3: Dependency to upload the archive to S3.
        user: The authenticated user making the request.
        db: The database connection.
        sample_zip_path: Path to the default sample zip file.
        logger: The application logger.

    Returns:
        A response object containing the original eICR, a URL to download the
        zipped results, and details about the refined condition.
    """

    # STEP 1:
    # handle file upload
    if not sample_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find sample zip file to download.",
        )

    if uploaded_file:
        try:
            file = await validate_zip_file(file=uploaded_file)
        except ZipValidationError as e:
            logger.error(
                msg="ZipValidationError in validate_zip_file", extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
            )
        logger.info(
            msg="Running inline test using user-provided file",
            extra={"file": file.filename},
        )
    else:
        file = create_sample_zip_file(sample_zip_path=sample_zip_path)
        logger.info(
            msg="Running inline test using sample file", extra={"file": file.filename}
        )

    try:
        # STEP 2:
        # read xml and call the service layer
        original_xml_files = await read_xml_zip(file)
    except ZipValidationError as e:
        logger.error(msg="ZipValidationError in read_xml_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )
    except FileProcessingError as e:
        logger.error(msg="FileProcessingError in read_xml_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ZIP_READING_ERROR,
        )

    # get the user's jurisdiction_id to pass to inline_testing
    jd = user.jurisdiction_id

    # get the DbConfiguration row for the jurisdiction
    configuration = await get_configuration_by_id_db(id=id, jurisdiction_id=jd, db=db)
    if not configuration:
        raise HTTPException(
            status_code=404, detail="Configuration not found for jurisdiction."
        )

    # get the primary DbCondition row that is linked to the DbConfiguration for the jurisdiction
    primary_condition = await get_condition_by_id_db(
        id=configuration.condition_id, db=db
    )
    if not primary_condition:
        raise HTTPException(
            status_code=404, detail="Primary condition not found for configuration."
        )

    # if included_conditions is a list greater than 1, then fetch all conditions
    # in the list (which includes the primary condition) for the payload and
    # store the corresponding trace info
    if len(configuration.included_conditions) > 1:
        all_conditions_for_configuration = await get_included_conditions_db(
            included_conditions=configuration.included_conditions, db=db
        )
    else:
        all_conditions_for_configuration = [primary_condition]

    # call the testing service
    # business logic around **how** inline testing works is in services/testing.py
    try:
        result = await inline_testing(
            xml_files=original_xml_files,
            configuration=configuration,
            primary_condition=primary_condition,
            all_conditions=all_conditions_for_configuration,
            jurisdiction_id=jd,
            logger=logger,
        )
    except XMLValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=XML_FILE_ERROR
        )

    # STEP 3:
    # handle the service layer response
    if result["configuration_does_not_match_conditions"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["configuration_does_not_match_conditions"],
        )

    refined_document = result["refined_document"]
    if refined_document is None:
        logger.error(
            msg="Internal logic error: inline_testing returned no error but also no refined eICR."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the refinement process.",
        )

    condition_obj = refined_document.reportable_condition

    # STEP 4:
    # prepare files for zip and s3 upload
    s3_file_package = []
    s3_file_package.append(("CDA_eICR.xml", original_xml_files.eicr))
    s3_file_package.append(("CDA_RR.xml", original_xml_files.rr))

    eicr_filename, rr_filename = create_split_condition_filename(
        condition_name=condition_obj.display_name,
        condition_code=condition_obj.code,
    )

    s3_file_package.append((eicr_filename, refined_document.refined_eicr))
    s3_file_package.append((rr_filename, refined_document.refined_rr))
    # Generate HTML from refined XML
    try:
        xslt_stylesheet_path = get_path_to_xslt_stylesheet()
        html_bytes = transform_xml_to_html(
            refined_document.refined_eicr.encode("utf-8"), xslt_stylesheet_path, logger
        )
        filename_html = eicr_filename.replace(".xml", ".html")
        s3_file_package.append((filename_html, html_bytes.decode("utf-8")))
        logger.info(
            f"Successfully transformed XML to HTML for: {eicr_filename}",
            extra={
                "condition_code": condition_obj.code,
                "condition_name": condition_obj.display_name,
            },
        )
    except Exception as e:
        if "XSLTTransformationError" in str(type(e)):
            logger.error(
                f"Failed to transform XML to HTML for: {eicr_filename}",
                extra={
                    "condition_code": condition_obj.code,
                    "condition_name": condition_obj.display_name,
                    "error": str(e),
                },
            )
        else:
            logger.error(
                f"Unexpected error during XML to HTML transformation for: {eicr_filename}",
                extra={
                    "condition_code": condition_obj.code,
                    "condition_name": condition_obj.display_name,
                    "error": str(e),
                },
            )
        # Continue with XML only; do not include HTML file for this condition

    try:
        output_file_name, output_zip_buffer = create_output_zip(
            files=s3_file_package,
        )
    except Exception as e:
        logger.error(msg="Error in create_output_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating the results ZIP file during S3 packaging process.",
        )
    try:
        s3_key = await run_in_threadpool(
            upload_refined_files_to_s3,
            user.id,
            user.jurisdiction_id,
            output_zip_buffer,
            output_file_name,
            logger,
        )
    except Exception as e:
        logger.error(msg="Error uploading to S3.", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error uploading ZIP file to S3.",
        )

    # STEP 5:
    # construct and return the final response
    formatted_unrefined_eicr = strip_comments(normalize_xml(original_xml_files.eicr))
    formatted_refined_eicr = strip_comments(
        normalize_xml(refined_document.refined_eicr)
    )
    formatted_refined_rr = strip_comments(normalize_xml(refined_document.refined_rr))

    return ConfigurationTestResponse(
        original_eicr=formatted_unrefined_eicr,
        refined_download_key=output_file_name if s3_key else "",
        condition=Condition(
            code=condition_obj.code,
            display_name=condition_obj.display_name,
            refined_eicr=formatted_refined_eicr,
            refined_rr=formatted_refined_rr,
            stats=[
                f"eICR file size reduced by {
                    get_file_size_reduction_percentage(
                        unrefined_eicr=formatted_unrefined_eicr,
                        refined_eicr=formatted_refined_eicr,
                    )
                }%",
            ],
        ),
    )

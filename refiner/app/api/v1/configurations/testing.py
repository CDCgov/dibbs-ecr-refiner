import io
from collections.abc import Awaitable, Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.auth.middleware import get_logged_in_user
from app.api.validation.file_validation import (
    get_validated_file,
    get_validated_xml_files,
    validate_path_or_raise,
)
from app.core.exceptions import (
    XMLValidationError,
)
from app.db.conditions.db import get_condition_by_id_db, get_included_conditions_db
from app.db.configurations.db import get_configuration_by_id_db
from app.db.demo.model import Condition
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.aws.s3 import upload_refined_file_package
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import (
    ZipFileItem,
    ZipFilePackage,
    create_html_file,
    create_refined_ecr_zip_in_memory,
    create_refined_file_names,
)
from app.services.format import (
    format_xml_document_for_display,
)
from app.services.logger import get_logger
from app.services.sample_file import get_sample_zip_path
from app.services.testing import inline_testing

from .model import ConfigurationTestResponse

router = APIRouter(prefix="/test")


def _get_upload_zip() -> Callable[[DbUser, io.BytesIO, str, Logger], Awaitable[str]]:
    return upload_refined_file_package


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
    upload_zip: Callable[[DbUser, io.BytesIO, str, Logger], Awaitable[str]] = Depends(
        _get_upload_zip
    ),
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
        upload_zip: Dependency to upload the archive to S3.
        user: The authenticated user making the request.
        db: The database connection.
        sample_zip_path: Path to the default sample zip file.
        logger: The application logger.

    Returns:
        A response object containing the original eICR, a URL to download the
        zipped results, and details about the refined condition.
    """
    # List of files to bundle into the zip
    zip_package = ZipFilePackage()

    # Check that demo file path is valid
    validate_path_or_raise(path=sample_zip_path)

    # Validate and load the file
    file = await get_validated_file(
        uploaded_file=uploaded_file, demo_file_path=sample_zip_path, logger=logger
    )

    original_xml_files = await get_validated_xml_files(file=file, logger=logger)

    # get the DbConfiguration row for the jurisdiction
    configuration = await get_configuration_by_id_db(
        id=id, jurisdiction_id=user.jurisdiction_id, db=db
    )
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
            jurisdiction_id=user.jurisdiction_id,
            logger=logger,
        )
    except XMLValidationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XML file(s) could not be processed. Please try again with valid XML files.",
        )

    # STEP 3:
    # handle the service layer response
    if result.configuration_does_not_match_conditions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.configuration_does_not_match_conditions,
        )

    refined_document = result.refined_document
    if refined_document is None:
        logger.error(
            msg="Internal logic error: inline_testing returned no error but also no refined eICR."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the refinement process.",
        )

    condition = refined_document.reportable_condition

    zip_package.add(
        ZipFileItem(file_name="CDA_eICR.xml", file_content=original_xml_files.eicr)
    )
    zip_package.add(
        ZipFileItem(file_name="CDA_RR.xml", file_content=original_xml_files.rr)
    )

    refined_file_names = create_refined_file_names(
        jurisdiction_id=user.jurisdiction_id,
        condition_name=condition.display_name,
    )

    html_file = create_html_file(
        condition=condition,
        refined_eicr=refined_document.refined_eicr,
        file_name=refined_file_names.eicr_html_file_name,
        logger=logger,
    )

    zip_package.add(
        ZipFileItem(
            file_name=refined_file_names.eicr_xml_file_name,
            file_content=refined_document.refined_eicr,
        )
    )
    zip_package.add(
        ZipFileItem(
            file_name=refined_file_names.rr_xml_file_name,
            file_content=refined_document.refined_rr,
        )
    )
    zip_package.add(html_file)

    output_file_name, output_zip_buffer = create_output_zip(
        zip_package=zip_package,
    )
    # Ship bundle to S3
    s3_key = await upload_zip(user, output_zip_buffer, output_file_name, logger)

    formatted_unrefined_eicr = format_xml_document_for_display(original_xml_files.eicr)
    formatted_refined_eicr = format_xml_document_for_display(
        refined_document.refined_eicr
    )

    return ConfigurationTestResponse(
        original_eicr=formatted_unrefined_eicr,
        refined_download_key=output_file_name if s3_key else "",
        condition=Condition(
            code=condition.code,
            display_name=condition.display_name,
            refined_eicr=formatted_refined_eicr,
            refined_rr=format_xml_document_for_display(refined_document.refined_rr),
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

import io
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from app.services.testing import independent_testing

from ...api.auth.middleware import get_logged_in_user
from ...core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ...db.demo.model import Condition, IndependentTestUploadResponse
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.model import DbUser
from ...services import file_io, format
from ...services.aws.s3 import upload_refined_ecr
from ...services.ecr.refine import get_file_size_reduction_percentage
from ...services.logger import get_logger
from ...services.sample_file import create_sample_zip_file, get_sample_zip_path
from ..validation.file_validation import validate_zip_file

# create a router instance for this file
router = APIRouter(prefix="/demo")


@router.post(
    "/upload",
    response_model=IndependentTestUploadResponse,
    tags=["demo"],
    operation_id="uploadEcr",
)
async def demo_upload(
    uploaded_file: UploadFile | None = File(None),
    demo_zip_path: Path = Depends(get_sample_zip_path),
    create_output_zip: Callable[..., tuple[str, io.BytesIO]] = Depends(
        lambda: file_io.create_refined_ecr_zip_in_memory
    ),
    user: DbUser = Depends(get_logged_in_user),
    upload_refined_files_to_s3: Callable[
        [UUID, io.BytesIO, str, Logger], str
    ] = Depends(lambda: upload_refined_ecr),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> IndependentTestUploadResponse:
    """
    Handles the demo upload workflow for eICR refinement.

    Steps:
    1. Obtain the demo eICR ZIP file (either uploaded by user or from local sample in
        refiner/assets/demo/mon-mothma-two-conditions.zip).
    2. Read and validate the XML files (eICR and RR) from the ZIP (XMLFiles object).
    3. Call the service layer (`independent_testing`) to orchestrate the refinement workflow.
    4. For each unique reportable condition code found in the RR (and having a configuration),
        build a refined XML document and collect metadata. The code used is the actual code
        from the RR that triggered the match, not a canonical or database code.
    5. Package all refined and original files into a ZIP.
    6. Upload the ZIP to S3 and get a download URL.
    7. Construct and return the response model for the frontend, including per-condition
        refinement results and a link to the ZIP of outputs.

    Any exceptions during file processing or workflow execution are caught and mapped to HTTP errors.
    """

    # STEP 1:
    # obtain demo file (upload or local sample)
    if not demo_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )

    # STEP 2:
    # validate and load the file
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
    else:
        file = create_sample_zip_file(sample_zip_path=demo_zip_path)

    try:
        logger.info("Processing demo file", extra={"upload_file": file.filename})

        # get jurisdiction_id from user
        jd = user.jurisdiction_id

        try:
            original_xml_files = await file_io.read_xml_zip(file)
        except ZipValidationError as e:
            logger.error("ZipValidationError in read_xml_zip", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
            )
        except XMLValidationError as e:
            logger.error("XMLValidationError in read_xml_zip", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="XML file(s) could not be processed.",
            )
        except FileProcessingError as e:
            logger.error("FileProcessingError in read_xml_zip", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File cannot be processed. Please ensure ZIP archive only contains the required files.",
            )

        # STEP 3:
        # orchestrate refinement workflow via service layer
        result = await independent_testing(
            db=db,
            xml_files=original_xml_files,
            jurisdiction_id=jd,
        )
        refined_documents = result["refined_documents"]
        conditions_without_matching_config_names = [
            missing_condition["display_name"]
            for missing_condition in result["no_matching_configuration_for_conditions"]
        ]

        # STEP 4:
        # for each unique reportable condition code found in the RR (with a config),
        # build a refined XML and collect metadata. The code used is from the RR.
        conditions: list[Condition] = []
        refined_files_to_zip = []
        for refined_document in refined_documents:
            condition_obj = refined_document.reportable_condition
            condition_refined_eicr = format.normalize_xml(refined_document.refined_eicr)

            condition_code = condition_obj.code
            condition_name = condition_obj.display_name

            filename = file_io.create_split_condition_filename(
                condition_name=condition_name, condition_code=condition_code
            )

            refined_files_to_zip.append((filename, condition_refined_eicr))

            stripped_refined_eicr = format.strip_comments(condition_refined_eicr)

            conditions.append(
                Condition(
                    code=condition_code,
                    display_name=condition_name,
                    refined_eicr=stripped_refined_eicr,
                    stats=[
                        f"eICR file size reduced by {
                            get_file_size_reduction_percentage(
                                unrefined_eicr=original_xml_files.eicr,
                                refined_eicr=condition_refined_eicr,
                            )
                        }%",
                    ],
                )
            )

        # STEP 5:
        # add original eICR + RR files to ZIP
        refined_files_to_zip.append(("CDA_eICR.xml", original_xml_files.eicr))
        refined_files_to_zip.append(("CDA_RR.xml", original_xml_files.rr))

        # STEP 6:
        # package files into ZIP and upload to S3
        output_file_name, output_zip_buffer = create_output_zip(
            files=refined_files_to_zip,
        )
        presigned_s3_url = await run_in_threadpool(
            upload_refined_files_to_s3,
            user.id,
            output_zip_buffer,
            output_file_name,
            logger,
        )

        # STEP 7:
        # construct and return the response model
        formatted_unrefined_eicr = format.strip_comments(
            format.normalize_xml(original_xml_files.eicr)
        )
        return IndependentTestUploadResponse(
            message="Successfully processed eICR with condition-specific refinement",
            refined_conditions_found=len(conditions),
            refined_conditions=conditions,
            conditions_without_matching_configs=conditions_without_matching_config_names,
            unrefined_eicr=formatted_unrefined_eicr,
            refined_download_url=presigned_s3_url,
        )
    except Exception as e:
        logger.error("Exception", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error occurred. Please check your file and try again.",
        )


@router.get("/download")
async def demo_download(
    file_path: Path = Depends(get_sample_zip_path), logger: Logger = Depends(get_logger)
) -> FileResponse:
    """
    Download the unrefined sample eCR zip file.
    """

    # Grab demo zip and send it along to the client
    if not Path(file_path).exists():
        logger.error("Demo file couldn't be downloaded.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )
    filename = file_path.name
    logger.info("Demo file downloaded successfully.")
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )

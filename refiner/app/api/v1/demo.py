import io
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from ...api.auth.middleware import get_logged_in_user
from ...core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ...db.demo.model import Condition, RefinedTestingDocument
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.model import DbUser
from ...services import file_io, format
from ...services.aws.s3 import upload_refined_ecr
from ...services.ecr.refine import get_file_size_reduction_percentage, refine
from ...services.logger import get_logger
from ...services.sample_file import create_sample_zip_file, get_sample_zip_path
from ..validation.file_validation import validate_zip_file

# create a router instance for this file
router = APIRouter(prefix="/demo")


def _get_zip_creator() -> Callable[..., tuple[str, io.BytesIO]]:
    """
    Dependency-injected function responsible for passing the function that will write the output zip file to the handler.

    Returns:
        A callable that takes a list of (filename, content) tuples and an output directory,
        and returns a tuple (zip_filename, zip_filepath, token).
    """
    return file_io.create_refined_ecr_zip_in_memory


def _get_upload_refined_ecr() -> Callable[[UUID, io.BytesIO, str, Logger], str]:
    """
    Provides a dependency-injectable reference to the `upload_refined_ecr` function.

    Returns:
        Callable[[UUID, io.BytesIO, str], str]: A callable that uploads a
        file to S3 and returns a pre-signed download URL. The arguments are:
            - user_id (UUID): The ID of the uploading user.
            - file_buffer (io.BytesIO): The in-memory ZIP file to upload.
            - filename (str): Filename for the uploaded file.
            - logger (Logger): The standard logger
    """
    return upload_refined_ecr


@router.post(
    "/upload",
    response_model=RefinedTestingDocument,
    tags=["demo"],
    operation_id="uploadEcr",
)
async def demo_upload(
    uploaded_file: UploadFile | None = File(None),
    demo_zip_path: Path = Depends(get_sample_zip_path),
    create_output_zip: Callable[..., tuple[str, io.BytesIO]] = Depends(
        _get_zip_creator
    ),
    user: DbUser = Depends(get_logged_in_user),
    upload_refined_files_to_s3: Callable[
        [UUID, io.BytesIO, str, Logger], str
    ] = Depends(_get_upload_refined_ecr),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> RefinedTestingDocument:
    """
    Grabs an eCR zip file from the file system and runs it through the upload/refine process.
    """

    # Grab the demo zip file and turn it into an UploadFile
    if not demo_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )

    file = None
    if uploaded_file:
        file = await validate_zip_file(file=uploaded_file)
    else:
        file = create_sample_zip_file(sample_zip_path=demo_zip_path)

    try:
        logger.info("Processing demo file", extra={"upload_file": file.filename})

        jd = user.jurisdiction_id

        # Refine each pair and collect results
        original_xml_files = await file_io.read_xml_zip(file)
        refined_results = await refine(
            original_xml=original_xml_files,
            db=db,
            jurisdiction_id=jd,
        )

        conditions = []
        refined_files_to_zip = []

        # Track condition metadata and gather refined XMLs to zip
        for result in refined_results:
            condition_code = result.reportable_condition.code
            condition_name = result.reportable_condition.display_name
            condition_refined_eicr = format.normalize_xml(result.refined_eicr)

            # Construct a filename for each XML (e.g. "covid_840539006.xml")
            filename = file_io.create_split_condition_filename(
                condition_name=condition_name, condition_code=condition_code
            )

            # Add to the list of files to include in the ZIP
            refined_files_to_zip.append((filename, condition_refined_eicr))

            # Strip comments afer adding to zip download for diff view
            stripped_refined_eicr = format.strip_comments(condition_refined_eicr)

            # Build per-condition metadata (zip token added later)
            conditions.append(
                Condition(
                    code=condition_code,
                    display_name=condition_name,
                    refined_eicr=stripped_refined_eicr,
                    stats=[
                        f"eICR file size reduced by {
                            get_file_size_reduction_percentage(
                                original_xml_files.eicr, condition_refined_eicr
                            )
                        }%",
                    ],
                )
            )

        # Add eICR + RR file as well
        refined_files_to_zip.append(("CDA_eICR.xml", original_xml_files.eicr))
        refined_files_to_zip.append(("CDA_RR.xml", original_xml_files.rr))

        # Now create the combined zip
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

        normalized_unrefined_eicr = format.normalize_xml(original_xml_files.eicr)
        stripped_unrefined_eicr = format.strip_comments(normalized_unrefined_eicr)

        return RefinedTestingDocument(
            message="Successfully processed eICR with condition-specific refinement",
            conditions_found=len(conditions),
            conditions=conditions,
            unrefined_eicr=stripped_unrefined_eicr,
            processing_notes=[
                "Each condition gets its own refined eICR",
                "Sections contain only data relevant to that specific condition",
                "Clinical codes matched using ProcessedGrouper database",
            ],
            refined_download_url=presigned_s3_url,
        )
    except XMLValidationError as e:
        logger.error("XMLValidationError", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XML file(s) could not be processed.",
        )
    except ZipValidationError as e:
        logger.error("ZipValidationError", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )
    except FileProcessingError as e:
        logger.error("FileProcessingError", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File cannot be processed. Please ensure ZIP archive only contains the required files.",
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

import io
import re
from collections.abc import Awaitable, Callable
from logging import Logger
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.api.auth.middleware import get_logged_in_user
from app.api.validation.file_validation import (
    get_validated_file,
    get_validated_xml_files,
    validate_path_or_raise,
)
from app.core.models.types import XMLFiles
from app.db.demo.model import Condition, IndependentTestUploadResponse
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.users.model import DbUser
from app.services.aws.s3 import (
    fetch_zip_from_s3,
    get_refined_user_zip_key,
    upload_refined_file_package,
)
from app.services.ecr.model import RefinedDocument
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import (
    ZipFileItem,
    ZipFilePackage,
    create_refined_ecr_zip_in_memory,
    create_refined_file_names,
)
from app.services.format import format_xml_document_for_display
from app.services.logger import get_logger
from app.services.sample_file import get_sample_zip_path
from app.services.testing import independent_testing
from app.services.xslt import create_refined_eicr_html_file

# Only allow:
# - letters
# - numbers
# - hyphens
# - underscores
# - periods
# - spaces
SAFE_FILENAME_RE = re.compile(r"^[\w\-. ]+\.zip$")

# create a router instance for this file
router = APIRouter(prefix="/demo")


def _get_upload_zip() -> Callable[[DbUser, io.BytesIO, str, Logger], Awaitable[str]]:
    return upload_refined_file_package


async def _build_refined_conditions(
    original_xml_files: XMLFiles,
    refined_documents: list[RefinedDocument],
    logger: Logger,
) -> tuple[list[Condition], list[ZipFileItem]]:
    """
    Builds a tuple that contains refined condition information along with the data required for zip file packaging.

    Args:
        original_xml_files (XMLFiles): The original eICR and RR
        jurisdiction_id (str): Jurisdiction ID of the logged in user
        refined_documents (list[RefinedDocument]): The list of refined documents
        logger (Logger): The logger

    Returns:
        tuple[list[Condition], list[ZippedItem]]: Refined condition list is the first item and the file packaging info is the second item.
    """

    # Return both of these at the end
    conditions: list[Condition] = []
    packaged_files: list[ZipFileItem] = []

    for refined_document in refined_documents:
        condition = refined_document.reportable_condition

        refined_file_names = create_refined_file_names(
            condition_name=condition.display_name,
        )

        # Package all refined files for condition
        packaged_files.append(
            ZipFileItem(
                file_name=refined_file_names.eicr_xml_file_name,
                file_content=refined_document.refined_eicr,
            )
        )

        packaged_files.append(
            ZipFileItem(
                file_name=refined_file_names.rr_xml_file_name,
                file_content=refined_document.refined_rr,
            )
        )

        html_file = create_refined_eicr_html_file(
            condition=condition,
            refined_eicr=refined_document.refined_eicr,
            file_name=refined_file_names.eicr_html_file_name,
            logger=logger,
        )

        packaged_files.append(html_file)

        formatted_refined_eicr = format_xml_document_for_display(
            refined_document.refined_eicr,
            preserve_comments=True,
        )

        conditions.append(
            Condition(
                code=condition.code,
                display_name=condition.display_name,
                refined_eicr=formatted_refined_eicr,
                refined_rr=format_xml_document_for_display(original_xml_files.rr),
                stats=[
                    f"eICR file size reduced by {
                        get_file_size_reduction_percentage(
                            unrefined_eicr=original_xml_files.eicr,
                            refined_eicr=refined_document.refined_eicr,
                        )
                    }%",
                ],
            )
        )
    return (conditions, packaged_files)


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
        lambda: create_refined_ecr_zip_in_memory
    ),
    user: DbUser = Depends(get_logged_in_user),
    upload_zip: Callable[[DbUser, io.BytesIO, str, Logger], Awaitable[str]] = Depends(
        _get_upload_zip
    ),
    db: AsyncDatabaseConnection = Depends(get_db),
    logger: Logger = Depends(get_logger),
) -> IndependentTestUploadResponse:
    """
    Handles the demo upload workflow for eICR refinement.

    Steps:
    1. Obtain the demo eICR ZIP file (either uploaded by user or from local sample in
        refiner/assets/demo/mon-mothma-covid-influenza.zip).
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

    # Check that demo file path is valid
    validate_path_or_raise(path=demo_zip_path)

    # Validate and load the file
    file = await get_validated_file(
        uploaded_file=uploaded_file, demo_file_path=demo_zip_path, logger=logger
    )

    logger.info("Processing independent test file", extra={"file": file.filename})

    original_xml_files = await get_validated_xml_files(file=file, logger=logger)

    # Run the test
    try:
        test_results = await independent_testing(
            db=db,
            xml_files=original_xml_files,
            jurisdiction_id=user.jurisdiction_id,
            logger=logger,
        )
    except Exception as e:
        logger.error("Error in the independent testing flow", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error occurred. Please check your file and try again.",
        )

    # Get the refined condition info and file packages
    conditions, zip_file_items = await _build_refined_conditions(
        original_xml_files=original_xml_files,
        refined_documents=test_results.refined_documents,
        logger=logger,
    )

    # List of files to bundle into the zip
    zip_package = ZipFilePackage(name=f"{test_results.original_eicr_doc_id}.zip")

    # Package refined files
    for item in zip_file_items:
        zip_package.add(item)

    # Package original files
    zip_package.add(
        ZipFileItem(file_name="CDA_eICR.xml", file_content=original_xml_files.eicr)
    )
    zip_package.add(
        ZipFileItem(file_name="CDA_RR.xml", file_content=original_xml_files.rr)
    )

    # Add shadow RR (for inactive conditions) to zip
    if test_results.shadow_rr:
        zip_package.add(
            ZipFileItem(
                file_name="CDA_RR_unrefined_rr.xml", file_content=test_results.shadow_rr
            )
        )

    # Create the zip bundle
    output_file_name, output_zip_buffer = create_output_zip(
        zip_package=zip_package,
    )

    # Ship bundle to S3
    s3_key = await upload_zip(user, output_zip_buffer, output_file_name, logger)

    return IndependentTestUploadResponse(
        message="Successfully processed eICR with condition-specific refinement",
        refined_conditions_found=len(conditions),
        refined_conditions=conditions,
        conditions_without_matching_configs=test_results.get_condition_names_with_no_matching_config(),
        conditions_without_active_configs=test_results.get_condition_names_with_no_active_config(),
        unrefined_eicr=format_xml_document_for_display(
            original_xml_files.eicr, preserve_comments=True
        ),
        refined_download_key=output_file_name if s3_key else "",
    )


@router.get(
    "/download/{filename}",
    tags=["demo"],
    operation_id="downloadRefinedEcr",
)
async def download_refined_ecr(
    filename: str,
    user: DbUser = Depends(get_logged_in_user),
    s3_download: Callable[[str], dict] = Depends(lambda: fetch_zip_from_s3),
    logger: Logger = Depends(get_logger),
) -> StreamingResponse:
    """Stream refined eCR zip from S3 by filename.

    The client provides only the filename (e.g. `<uuid>_refined_ecr.zip`). The
    server constructs the S3 object key based on the authenticated user.
    """

    if not SAFE_FILENAME_RE.match(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename."
        )

    key = get_refined_user_zip_key(
        user_id=user.id,
        jurisdiction_id=user.jurisdiction_id,
        filename=filename,
    )

    try:
        resp = await run_in_threadpool(s3_download, key)
    except Exception as e:
        logger.error(
            "Failed to fetch refined zip from S3",
            extra={"error": str(e), "key": key, "filename": filename},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    body = resp.get("Body")
    if body is None or not hasattr(body, "iter_chunks"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    download_name = filename
    return StreamingResponse(
        content=body.iter_chunks(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )

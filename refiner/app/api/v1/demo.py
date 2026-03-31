import io
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.api.validation.file_validation import (
    get_validated_file,
    get_validated_xml_files,
    validate_path_or_raise,
)
from app.core.models.types import XMLFiles
from app.services.ecr.model import RefinedDocument, ReportableCondition
from app.services.testing import independent_testing

from ...api.auth.middleware import get_logged_in_user
from ...db.demo.model import Condition, IndependentTestUploadResponse
from ...db.pool import AsyncDatabaseConnection, get_db
from ...db.users.model import DbUser
from ...services import file_io, format
from ...services.aws.s3 import (
    fetch_zip_from_s3,
    get_refined_user_zip_key,
    upload_refined_ecr,
)
from ...services.ecr.refine import get_file_size_reduction_percentage
from ...services.logger import get_logger
from ...services.sample_file import get_sample_zip_path
from ...services.xslt import (
    XSLTTransformationError,
    get_path_to_xslt_stylesheet,
    transform_xml_to_html,
)

# create a router instance for this file
router = APIRouter(prefix="/demo")

XML_FILE_ERROR = (
    "XML file(s) could not be processed. Please try again with valid XML files.",
)
ZIP_READING_ERROR = (
    "ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present and can't be empty files.",
)
FILE_PROCESSING_ERROR = (
    "File cannot be processed. Please ensure ZIP archive only contains the required files.",
)
GENERIC_SERVER_ERROR = ("Server error occurred. Please check your file and try again.",)

type ZippedItem = tuple[str, str]


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
        [UUID, str, io.BytesIO, str, Logger], str
    ] = Depends(lambda: upload_refined_ecr),
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

    # List of files to bundle into the zip
    packaged_files: list[ZippedItem] = []

    # Check that demo file path is valid
    validate_path_or_raise(path=demo_zip_path)

    # Validate and load the file
    file = await get_validated_file(
        uploaded_file=uploaded_file, demo_file_path=demo_zip_path, logger=logger
    )

    logger.info("Processing demo file", extra={"upload_file": file.filename})

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
            detail=GENERIC_SERVER_ERROR,
        )

    # Get the refined condition info and file packages
    conditions, refined_file_packages = _build_refined_conditions(
        original_xml_files=original_xml_files,
        refined_documents=test_results.refined_documents,
        logger=logger,
    )

    # Package refined files
    for item in refined_file_packages:
        packaged_files.append(item)

    # Package original files
    packaged_files.append(("CDA_eICR.xml", original_xml_files.eicr))
    packaged_files.append(("CDA_RR.xml", original_xml_files.rr))

    # Create the zip bundle
    output_file_name, output_zip_buffer = create_output_zip(
        files=packaged_files,
    )

    # Ship bundle to S3
    output_key = await run_in_threadpool(
        upload_refined_files_to_s3,
        user.id,
        user.jurisdiction_id,
        output_zip_buffer,
        output_file_name,
        logger,
    )

    return IndependentTestUploadResponse(
        message="Successfully processed eICR with condition-specific refinement",
        refined_conditions_found=len(conditions),
        refined_conditions=conditions,
        conditions_without_matching_configs=test_results.get_condition_names_with_no_matching_config(),
        conditions_without_active_configs=test_results.get_condition_names_with_no_active_config(),
        unrefined_eicr=_format_xml_document(original_xml_files.eicr),
        refined_download_key=output_file_name if output_key else "",
    )


def _build_refined_conditions(
    original_xml_files: XMLFiles,
    refined_documents: list[RefinedDocument],
    logger: Logger,
) -> tuple[list[Condition], list[ZippedItem]]:
    """
    Builds a list of refined conditions.

    Args:
        original_xml_files (XMLFiles): The original eICR and RR
        refined_documents (list[RefinedDocument]): The list of refined documents
        logger (Logger): The logger

    Returns:
        tuple[list[Condition], list[ZippedItem]]: Refined condition list is the first item and the file packaging info is the second item.
    """

    # Return both of these at the end
    conditions: list[Condition] = []
    packaged_files: list[ZippedItem] = []

    for refined_document in refined_documents:
        condition = refined_document.reportable_condition

        refined_file_names = file_io.create_refined_file_names(
            condition_name=condition.display_name,
            condition_code=condition.code,
        )

        html_file = _create_html_file(
            condition=condition,
            refined_eicr=refined_document.refined_eicr,
            file_name=refined_file_names.eicr_html_file_name,
            logger=logger,
        )

        # Package all refined files for condition
        packaged_files.append(
            (refined_file_names.eicr_xml_file_name, refined_document.refined_eicr)
        )
        packaged_files.append(
            (refined_file_names.rr_xml_file_name, refined_document.refined_rr)
        )
        packaged_files.append(html_file)

        formatted_refined_eicr = _format_xml_document(refined_document.refined_eicr)

        conditions.append(
            Condition(
                code=condition.code,
                display_name=condition.display_name,
                refined_eicr=formatted_refined_eicr,
                refined_rr=_format_xml_document(original_xml_files.rr),
                stats=[
                    f"eICR file size reduced by {
                        get_file_size_reduction_percentage(
                            unrefined_eicr=_format_xml_document(
                                original_xml_files.eicr
                            ),
                            refined_eicr=formatted_refined_eicr,
                        )
                    }%",
                ],
            )
        )
    return (conditions, packaged_files)


def _format_xml_document(text: str) -> str:
    """
    Helper function to strip comments and perform normalization on a string.

    Args:
        text (str): XML document

    Returns:
        str: String with comments stripped and text normalized.
    """
    return format.strip_comments(format.normalize_xml(text))


def _create_html_file(
    condition: ReportableCondition, refined_eicr: str, file_name: str, logger: Logger
) -> ZippedItem:
    """
    Creates an HTML file using the refined condition information.

    Args:
        condition (ReportableCondition): The reportable condition
        refined_eicr (str): Condition's refined eICR document
        file_name (str): Desired HTML file name
        logger (Logger): The logger

    Returns:
        ZippedItem: A processed object ready for packing into a zip file.
    """
    try:
        xslt_stylesheet_path = get_path_to_xslt_stylesheet()
        html_bytes = transform_xml_to_html(
            refined_eicr.encode("utf-8"), xslt_stylesheet_path, logger
        )

        logger.info(
            f"Successfully transformed XML to HTML for condition: {condition.display_name}",
            extra={
                "condition_code": condition.code,
                "condition_name": condition.display_name,
            },
        )
    except XSLTTransformationError as e:
        logger.error(
            f"Failed to transform XML to HTML for condition: {condition.display_name}",
            extra={
                "condition_code": condition.code,
                "condition_name": condition.display_name,
                "error": str(e),
            },
        )
    return (file_name, html_bytes.decode("utf-8"))


@router.get(
    "/download/{filename}",
    tags=["demo"],
    operation_id="downloadRefinedEcr",
)
async def download_refined_ecr(
    filename: str,
    user: DbUser = Depends(get_logged_in_user),
    s3_download: Callable[[str, Logger], dict] = Depends(lambda: fetch_zip_from_s3),
    logger: Logger = Depends(get_logger),
) -> StreamingResponse:
    """Stream refined eCR zip from S3 by filename.

    The client provides only the filename (e.g. `<uuid>_refined_ecr.zip`). The
    server constructs the S3 object key based on the authenticated user.
    """

    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename."
        )
    if not filename.endswith("_refined_ecr.zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename."
        )

    uuid_prefix = filename.removesuffix("_refined_ecr.zip")
    try:
        UUID(uuid_prefix)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    key = get_refined_user_zip_key(
        user_id=user.id,
        jurisdiction_id=user.jurisdiction_id,
        filename=filename,
    )

    try:
        resp = await run_in_threadpool(s3_download, key, logger)
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

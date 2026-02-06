import io
from collections.abc import Callable
from logging import Logger
from pathlib import Path
from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

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
from ...services.aws import s3
from ...services.ecr.refine import get_file_size_reduction_percentage
from ...services.logger import get_logger
from ...services.sample_file import create_sample_zip_file, get_sample_zip_path
from ...services.xslt import (
    XSLTTransformationError,
    get_path_to_xslt_stylesheet,
    transform_xml_to_html,
)
from ..validation.file_validation import validate_zip_file

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
    ] = Depends(lambda: s3.upload_refined_ecr),
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
                msg="ZipValidationError in validate_zip_file",
                extra={"error": str(e)},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
            )
    else:
        file = create_sample_zip_file(sample_zip_path=demo_zip_path)

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

    try:
        # STEP 3:
        # orchestrate refinement workflow via service layer
        result = await independent_testing(
            db=db,
            xml_files=original_xml_files,
            jurisdiction_id=jd,
            logger=logger,
        )
    except Exception as e:
        logger.error("Error in the independent testing flow", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=GENERIC_SERVER_ERROR,
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

        condition_code = condition_obj.code
        condition_name = condition_obj.display_name

        eicr_filename_xml, rr_filename_xml = file_io.create_split_condition_filename(
            condition_name=condition_name,
            condition_code=condition_code,
        )
        eicr_filename_html = eicr_filename_xml.replace(".xml", ".html")

        condition_refined_eicr = refined_document.refined_eicr
        condition_refined_rr = refined_document.refined_rr
        refined_files_to_zip.append((eicr_filename_xml, condition_refined_eicr))
        refined_files_to_zip.append((rr_filename_xml, condition_refined_rr))

        # Try to generate HTML using XSLT
        try:
            xslt_stylesheet_path = get_path_to_xslt_stylesheet()
            html_bytes = transform_xml_to_html(
                condition_refined_eicr.encode("utf-8"), xslt_stylesheet_path, logger
            )
            refined_files_to_zip.append(
                (eicr_filename_html, html_bytes.decode("utf-8"))
            )
            logger.info(
                f"Successfully transformed XML to HTML for: {eicr_filename_xml}",
                extra={
                    "condition_code": condition_code,
                    "condition_name": condition_name,
                },
            )
        except XSLTTransformationError as e:
            logger.error(
                f"Failed to transform XML to HTML for: {eicr_filename_xml}",
                extra={
                    "condition_code": condition_code,
                    "condition_name": condition_name,
                    "error": str(e),
                },
            )
            # Continue with XML only; do not include HTML file for this condition

        normalized_refined_eicr = format.normalize_xml(refined_document.refined_eicr)
        refined_files_to_zip.append((eicr_filename_xml, normalized_refined_eicr))

        formatted_unrefined_eicr = format.strip_comments(
            format.normalize_xml(original_xml_files.eicr)
        )
        formatted_refined_eicr = format.strip_comments(normalized_refined_eicr)
        formatted_refined_rr = format.strip_comments(
            format.normalize_xml(original_xml_files.rr)
        )
        conditions.append(
            Condition(
                code=condition_code,
                display_name=condition_name,
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
    s3_key = await run_in_threadpool(
        upload_refined_files_to_s3,
        user.id,
        output_zip_buffer,
        output_file_name,
        logger,
    )
    if s3_key is None:
        s3_key = ""

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
        refined_download_key=s3_key,
    )


def _get_filename_from_key(key: str) -> str:
    return key.split("/")[-1] if "/" in key else key


@router.get(
    "/download/{key:path}",
    tags=["demo"],
    operation_id="downloadRefinedEcr",
)
async def download_refined_ecr(
    key: str,
    user: DbUser = Depends(get_logged_in_user),
    logger: Logger = Depends(get_logger),
) -> StreamingResponse:
    """
    Stream refined eCR zip from S3 for download by key.
    """
    from uuid import UUID

    s3_prefix = "refiner-test-suite"

    # enforce prefix
    parts = key.split("/")
    if len(parts) < 4 or parts[0] != s3_prefix:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this file.",
        )
    # enforce uuid
    try:
        UUID(parts[2])
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this file.",
        )
    # enforce ownership
    if str(user.id) != parts[2]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to download this file.",
        )
    try:
        s3_response = s3.fetch_zip_from_s3(key, logger)
    except ClientError as e:
        code = ""
        msg = str(e)
        if hasattr(e, "response") and e.response:
            code = e.response.get("Error", {}).get("Code", "")
            msg = e.response.get("Error", {}).get("Message", msg)
        if not code and not msg.strip():
            raise RuntimeError(
                "fetch_zip_from_s3 mock returned blank error, route logic expects dict not error. Patch returns not handled."
            )
        if (
            code == "NoSuchKey"
            or "NoSuchKey" in msg
            or "not exist" in msg
            or "not found" in msg
        ):
            raise HTTPException(404, detail="File not found.")
        if (
            code in {"AccessDenied", "Forbidden"}
            or "AccessDenied" in msg
            or "Forbidden" in msg
            or "denied" in msg.lower()
            or "forbidden" in msg.lower()
        ):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to download this file.",
            )
        raise HTTPException(500, detail="An error occurred while retrieving the file.")
    filename = _get_filename_from_key(key)
    logger.info(
        "Streaming file download",
        extra={"key": key, "user_id": str(user.id), "download_filename": filename},
    )
    return StreamingResponse(
        content=s3_response["Body"].iter_chunks(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

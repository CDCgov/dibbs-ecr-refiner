import asyncio
import io
import os
import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.datastructures import Headers
from fastapi.responses import FileResponse

from ...core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ...db.demo.model import RefinedTestingDocument
from ...db.pool import AsyncDatabaseConnection, get_db
from ...services import file_io, format
from ...services.ecr.refine import refine_async

# Keep track of files available for download / what needs to be cleaned up
REFINED_ECR_DIR = "refined-ecr"
FILE_NAME_SUFFIX = "refined_ecr.zip"
file_store: dict[str, dict] = {}

# File uploads
MAX_ALLOWED_UPLOAD_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ALLOWED_UNCOMPRESSED_FILE_SIZE = MAX_ALLOWED_UPLOAD_FILE_SIZE * 5  # 50 MB

# create a router instance for this file
router = APIRouter(prefix="/demo")


async def run_expired_file_cleanup_task() -> None:
    """
    Runs a task to delete files in the `refined-ecr` directory.

    This function will run periodically within its own thread upon application startup, configured in `main.py`
    """
    seconds = 120  # 2 minutes
    while True:
        await asyncio.to_thread(_cleanup_expired_files)
        await asyncio.sleep(seconds)


def _cleanup_expired_files() -> None:
    """
    Attempts to clean up files that exist beyond their time-to-live value (2 minutes) according to their `timestamp`.
    """
    file_ttl_seconds = 120  # 2 minutes
    now = time.time()

    to_delete = [
        key
        for key, meta in file_store.items()
        if now - meta["timestamp"] > file_ttl_seconds
    ]
    for key in to_delete:
        try:
            os.remove(file_store[key]["path"])
        except FileNotFoundError:
            pass
        del file_store[key]


def _get_demo_zip_path() -> Path:
    """
    Get the path to the demo ZIP file.
    """

    return file_io.get_asset_path("demo", "mon-mothma-two-conditions.zip")


def _create_zipfile_output_directory(base_path: Path) -> Path:
    """
    Creates (if needed) and returns the path to the directory where refined eCRs live.
    """

    if not os.path.exists(base_path):
        os.mkdir(base_path)

    return base_path


def _get_file_size_difference_percentage(
    unrefined_document: str, refined_document: str
) -> int:
    unrefined_bytes = len(unrefined_document.encode("utf-8"))
    refined_bytes = len(refined_document.encode("utf-8"))

    if unrefined_bytes == 0:
        return 0

    percent_diff = (unrefined_bytes - refined_bytes) / unrefined_bytes * 100
    return round(percent_diff)


def _create_refined_ecr_zip(
    *,
    files: list[tuple[str, str]],
    output_dir: Path,
) -> tuple[str, Path, str]:
    """
    Create a zip archive containing all provided (filename, content) pairs.

    Args:
        files (list): List of tuples [(filename, content)], content must be string.
        output_dir (Path): Directory to save the zip file.

    Returns:
        (filename, filepath, token)
    """
    token = str(uuid4())
    zip_filename = f"{token}_refined_ecr.zip"
    zip_filepath = output_dir / zip_filename

    with ZipFile(zip_filepath, "w") as zf:
        for filename, content in files:
            zf.writestr(filename, content)

    return zip_filename, zip_filepath, token


def _update_file_store(filename: str, path: Path, token: str) -> None:
    """
    Updates the in-memory dictionary with required metadata for the refined eCR available to download.

    This information is used by `_cleanup_expired_files()` in order to delete expired eCR zip files.

    Args:
        filename: name of the file to keep track of
        path: full path of the file to keep track of
        token: a unique token to identify the file
    """
    file_store[token] = {
        "path": path,
        "timestamp": time.time(),
        "filename": filename,
    }


def _get_zip_creator() -> Callable[..., tuple[str, Path, str]]:
    """
    Dependency-injected function responsible for passing the function that will write the output zip file to the handler.

    Returns:
        A callable that takes a list of (filename, content) tuples and an output directory,
        and returns a tuple (zip_filename, zip_filepath, token).
    """
    return _create_refined_ecr_zip


def _get_refined_ecr_output_dir() -> Path:
    """
    Dependency injected function responsible for getting the processed eCR output directory path.
    """
    return Path(REFINED_ECR_DIR)


def _create_sample_zip_file(demo_zip_path: Path) -> UploadFile:
    filename = demo_zip_path.name
    with open(demo_zip_path, "rb") as demo_file:
        zip_content = demo_file.read()

    file_like = io.BytesIO(zip_content)
    file_like.seek(0)
    file = UploadFile(
        file=file_like,
        filename=filename,
        headers=Headers({"Content-Type": "application/zip"}),
    )
    return file


async def _validate_zip_file(file: UploadFile) -> UploadFile:
    # Check extension
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip files are allowed.",
        )

    # Name safety check
    if file.filename.startswith("."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot start with a period (.).",
        )

    # Name safety check
    if ".." in file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot contain multiple periods (.) in a row",
        )

    # Ensure file has content
    if file.size is None or file.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=".zip must not be empty.",
        )

    # Ensure compressed size is valid
    if file.size > MAX_ALLOWED_UPLOAD_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=".zip file must be less than 10MB in size.",
        )

    return file


@router.post(
    "/upload",
    response_model=RefinedTestingDocument,
    tags=["demo"],
    operation_id="uploadEcr",
)
async def demo_upload(
    uploaded_file: UploadFile | None = File(None),
    demo_zip_path: Path = Depends(_get_demo_zip_path),
    create_output_zip: Callable[..., tuple[str, Path, str]] = Depends(_get_zip_creator),
    refined_zip_output_dir: Path = Depends(_get_refined_ecr_output_dir),
    db: AsyncDatabaseConnection = Depends(get_db),
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
        file = await _validate_zip_file(file=uploaded_file)
    else:
        file = _create_sample_zip_file(demo_zip_path=demo_zip_path)

    try:
        # Refine each pair and collect results
        original_xml_files = await file_io.read_xml_zip(file)
        refined_results = await refine_async(original_xml=original_xml_files, db=db)

        conditions = []
        refined_files_to_zip = []

        # Track condition metadata and gather refined XMLs to zip
        for result in refined_results:
            condition_code = result.reportable_condition.code
            condition_name = result.reportable_condition.display_name
            condition_refined_eicr = result.refined_eicr

            # Construct a filename for each XML (e.g. "covid_840539006.xml")
            safe_name = condition_name.replace(" ", "_").replace("/", "_")
            filename = f"CDA_eICR_{condition_code}_{safe_name}.xml"

            # Add to the list of files to include in the ZIP
            refined_files_to_zip.append((filename, condition_refined_eicr))

            # Build per-condition metadata (zip token added later)
            conditions.append(
                {
                    "code": condition_code,
                    "display_name": condition_name,
                    "refined_eicr": format.normalize_xml(condition_refined_eicr),
                    "stats": [
                        f"eICR file size reduced by {
                            _get_file_size_difference_percentage(
                                original_xml_files.eicr, condition_refined_eicr
                            )
                        }%",
                    ],
                    "processing_info": {
                        "condition_specific": True,
                        "sections_processed": "All sections scoped to condition codes",
                        "method": "ProcessedGrouper-based filtering",
                    },
                }
            )

        # ✅ Zip all condition files + eICR file into one archive
        full_zip_output_path = _create_zipfile_output_directory(refined_zip_output_dir)

        # Add eICR + RR file as well
        refined_files_to_zip.append(("CDA_eICR.xml", original_xml_files.eicr))
        refined_files_to_zip.append(("CDA_RR.xml", original_xml_files.rr))

        # Now create the combined zip
        output_file_name, output_file_path, token = create_output_zip(
            files=refined_files_to_zip,
            output_dir=full_zip_output_path,
        )

        # Store the combined zip
        _update_file_store(output_file_name, output_file_path, token)

        normalized_unrefined_eicr = format.normalize_xml(original_xml_files.eicr)

        return RefinedTestingDocument(
            message="Successfully processed eICR with condition-specific refinement",
            conditions_found=len(conditions),
            conditions=conditions,
            unrefined_eicr=normalized_unrefined_eicr,
            processing_notes=[
                "Each condition gets its own refined eICR",
                "Sections contain only data relevant to that specific condition",
                "Clinical codes matched using ProcessedGrouper database",
            ],
            refined_download_token=token,
        )
    except XMLValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XML file(s) could not be processed.",
        )
    except ZipValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )
    except FileProcessingError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File cannot be processed. Please ensure ZIP archive only contains the required files.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error occurred. Please check your file and try again.",
        )
    except ZipValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.details)


@router.get("/download/{token}", tags=["demo"], operation_id="downloadRefinedEcr")
async def download_refined_ecr(token: str) -> FileResponse:
    """
    Download a refined eCR zip file given a unique token.
    """

    if token not in file_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or has expired.",
        )

    file_path = file_store[token]["path"]
    filename = file_store[token]["filename"]

    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )


@router.get("/download", tags=["demo"], operation_id="downloadSampleEcr")
async def demo_download(file_path: Path = Depends(_get_demo_zip_path)) -> FileResponse:
    """
    Download the unrefined sample eCR zip file.
    """

    # Grab demo zip and send it along to the client
    if not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )
    filename = file_path.name
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )

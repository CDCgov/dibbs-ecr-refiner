import asyncio
import io
import os
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from zipfile import ZipFile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.datastructures import Headers
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from ...core.exceptions import XMLValidationError
from ...services import file_io, refine

# Keep track of files available for download / what needs to be cleaned up
REFINED_ECR_DIR = "refined-ecr"
FILE_NAME_SUFFIX = "refined_ecr.zip"
file_store: dict[str, dict] = {}

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
    *, files: list[tuple[str, str]], output_dir: Path
) -> tuple[str, Path, str]:
    """
    Create a zip archive containing all provided (filename, content) pairs.

    Args:
        files (list): List of tuples [(filename, content)], content must be string.
        output_dir (Path): Directory to save the zip file.

    Returns:
        (filename, filepath, token)
    """
    from uuid import uuid4
    import os

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


def _get_zip_creator() -> Callable[
    [list[tuple[str, str]], Path], tuple[str, Path, str]
]:
    """
    Dependency-injected function responsible for passing the function that will write
    the output zip file to the handler.

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


@router.get("/upload")
async def demo_upload(
    demo_zip_path: Path = Depends(_get_demo_zip_path),
    create_output_zip: Callable[[str, str, Path], tuple[str, Path, str]] = Depends(
        _get_zip_creator
    ),
    refined_zip_output_dir: Path = Depends(_get_refined_ecr_output_dir),
) -> JSONResponse:
    """
    Grabs an eCR zip file from the file system and runs it through the upload/refine process.
    """

    # Grab the demo zip file and turn it into an UploadFile
    if not demo_zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )

    filename = demo_zip_path.name
    with open(demo_zip_path, "rb") as demo_file:
        zip_content = demo_file.read()

    file_like = io.BytesIO(zip_content)
    file_like.seek(0)
    upload_file = UploadFile(
        file=file_like,
        filename=filename,
        headers=Headers({"Content-Type": "application/zip"}),
    )

    try:
        # Read in and process XML data from demo file
        original_xml_files = await file_io.read_xml_zip(upload_file)
        rr_results = refine.process_rr(original_xml_files)
        reportable_conditions = rr_results["reportable_conditions"]

        # create condition-eICR pairs with XMLFiles objects
        condition_eicr_pairs = refine.build_condition_eicr_pairs(
            original_xml_files, reportable_conditions
        )

        # Refine each pair and collect results
        refined_results = []

        # for each reportable condition, create a separate XMLFiles copy and refine independently.
        # this ensures output isolation: each condition produces its own eICR, with only the data relevant to that condition.
        # using a fresh XMLFiles object per condition also makes it straightforward to support future workflows,
        # such as processing and returning RR (Reportability Response) documents alongside or in relation to each eICR.
        for pair in condition_eicr_pairs:
            condition = pair["reportable_condition"]
            xml_files = pair[
                "xml_files"
            ]  # Each pair contains a distinct XMLFiles instance.

            # refine the eICR for this specific condition code.
            refined_eicr = refine.refine_eicr(
                xml_files=xml_files,
                condition_codes=condition["code"],
            )

            # collect the refined result for this condition.
            refined_results.append(
                {
                    "reportable_condition": condition,
                    "refined_eicr": refined_eicr,
                }
            )

        # build the response so each output is clearly associated with its source condition.
        # this structure makes it easy for clients to consume and extends naturally if we later return RR artifacts.
        conditions = []
        refined_files_to_zip = []

        # Track condition metadata and gather refined XMLs to zip
        for idx, result in enumerate(refined_results):
            condition_info = result["reportable_condition"]
            condition_refined_eicr = result["refined_eicr"]

            # Construct a filename for each XML (e.g. "covid_840539006.xml")
            condition_code = condition_info.get("code", f"cond_{idx}")
            display_name = condition_info.get("displayName", f"Condition_{idx}")
            safe_name = display_name.replace(" ", "_").replace("/", "_")
            filename = f"{condition_code}_{safe_name}.xml"

            # Add to the list of files to include in the ZIP
            refined_files_to_zip.append((filename, condition_refined_eicr))

            # Build per-condition metadata (zip token added later)
            conditions.append(
                {
                    "code": condition_info["code"],
                    "display_name": condition_info["displayName"],
                    "refined_eicr": condition_refined_eicr,
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

        # Add eICR file as well
        refined_files_to_zip.append(("CDA_EICR.xml", xml_files.eicr))

        # Now create the combined zip
        output_file_name, output_file_path, token = create_output_zip(
            files=refined_files_to_zip,
            output_dir=full_zip_output_path,
        )

        # Store the combined zip
        _update_file_store(output_file_name, output_file_path, token)

        return JSONResponse(
            content=jsonable_encoder(
                {
                    "message": "Successfully processed eICR with condition-specific refinement",
                    "conditions_found": len(conditions),
                    "conditions": conditions,
                    "unrefined_eicr": original_xml_files.eicr,
                    "processing_notes": [
                        "Each condition gets its own refined eICR",
                        "Sections contain only data relevant to that specific condition",
                        "Clinical codes matched using ProcessedGrouper database",
                    ],
                    "refined_download_token": token,
                }
            )
        )
    except XMLValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "details": e.details},
        )


@router.get("/download/{token}")
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


@router.get("/download")
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

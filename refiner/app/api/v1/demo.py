import asyncio
import io
import os
import time
import uuid
from pathlib import Path
from zipfile import ZipFile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from ...core.exceptions import XMLValidationError
from ...services import file_io, refine

# Keep track of files available for download / what needs to be cleaned up
FILE_NAME_SUFFIX = "refined_ecr.zip"
file_store: dict[str, dict] = {}

# create a router instance for this file
router = APIRouter(prefix="/demo")


async def run_expired_file_cleanup_task() -> None:
    """
    Runs a task to delete files in the `refined-ecr` directory every 5 minutes.

    This function will run periodically within its own thread upon application startup.
    """
    seconds = 300  # 5 minutes
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

    return file_io.get_asset_path("demo", "monmothma.zip")


def _get_processed_ecr_directory() -> Path:
    """
    Returns the path to the directory where refined eCRs live.

    This directory will be created if it doesn't already exist on the file system.
    """
    REFINED_ECR_DIR = "refined-ecr"
    if not os.path.exists(REFINED_ECR_DIR):
        os.mkdir(REFINED_ECR_DIR)

    return REFINED_ECR_DIR


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
    refined_eicr: str, unrefined_rr: str
) -> tuple[str, Path, str]:
    """
    Writes a zip file to disk containing the refined eICR and unrefined RR files.
    """
    token = str(uuid.uuid4())
    output_file_name = f"{token}_{FILE_NAME_SUFFIX}"

    output_dir = _get_processed_ecr_directory()
    output_file_path = Path(output_dir, output_file_name)

    with ZipFile(output_file_path, "w") as zf:
        zf.writestr("CDA_eICR.xml", refined_eicr)
        zf.writestr("CDA_RR.xml", unrefined_rr)

    return output_file_name, output_file_path, token


def _update_file_store(
    output_file_name: str, output_file_path: Path, token: str
) -> None:
    """
    Updates the dictionary with required metadata for the refined eCR available to download.

    This information is used by `_cleanup_expired_files()` in order to delete expired eCR zip files.
    """
    file_store[token] = {
        "path": output_file_path,
        "timestamp": time.time(),
        "filename": output_file_name,
    }


@router.get("/upload")
async def demo_upload(file_path: Path = Depends(_get_demo_zip_path)) -> JSONResponse:
    """
    Grabs an eCR zip file from the file system and runs it through the upload/refine process.
    """

    # Grab the demo zip file and turn it into an UploadFile
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )

    filename = file_path.name
    with open(file_path, "rb") as demo_file:
        zip_content = demo_file.read()

    file_like = io.BytesIO(zip_content)
    file_like.seek(0)
    upload_file = UploadFile(
        file=file_like,
        filename=filename,
        headers={"Content-Type": "application/zip"},
    )

    try:
        xml_files = await file_io.read_xml_zip(upload_file)
        rr_results = refine.process_rr(xml_files)
        refined_eicr = refine.refine_eicr(xml_files)
        output_file_name, output_file_path, token = _create_refined_ecr_zip(
            refined_eicr, xml_files.rr
        )
        _update_file_store(output_file_name, output_file_path, token)

        return JSONResponse(
            content=jsonable_encoder(
                {
                    "unrefined_eicr": xml_files.eicr,
                    "refined_eicr": refined_eicr,
                    "reportable_conditions": rr_results["reportable_conditions"],
                    "stats": [
                        f"eCR file size reduced by {
                            _get_file_size_difference_percentage(
                                xml_files.eicr, refined_eicr
                            )
                        }%",
                        "Found X observations relevant to the condition(s)",
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

import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.refine import refine, validate_message
from app.utils import read_zip

router = APIRouter(prefix="/demo")


def _get_demo_zip_path() -> Path:
    return Path(__file__).parent.parent.parent / "assets" / "demo" / "monmothma.zip"


def _get_file_size_difference_percentage(
    unrefined_document: str, refined_document: str
) -> int:
    megabyte = 1024 * 1024
    unrefined_mb = len(unrefined_document.encode("utf-8")) / megabyte
    refined_mb = len(refined_document.encode("utf-8")) / megabyte

    if unrefined_mb == 0:
        return 0

    percent_diff = (unrefined_mb - refined_mb) / unrefined_mb * 100
    return round(percent_diff)


@router.get("/upload")
async def demo_upload(file_path: Path = Depends(_get_demo_zip_path)):
    """
    Grabs an eCR zip file from the file system and runs it through the upload/refine process.
    """
    # Grab the demo zip file and turn it into an UploadFile
    if not Path(file_path).exists():
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

    # Read the created UploadFile
    eicr_xml, _rr_xml = await read_zip(upload_file)
    validated_message, _error_message = validate_message(eicr_xml)
    refined_data = refine(validated_message, None, None)
    return Response(content=refined_data, media_type="application/xml")


@router.get("/download")
async def demo_download(file_path: Path = Depends(_get_demo_zip_path)):
    """
    Allows the user to download the sample eCR zip file.
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

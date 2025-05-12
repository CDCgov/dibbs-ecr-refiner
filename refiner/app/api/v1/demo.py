import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from ...core.exceptions import XMLValidationError
from ...services import file_io, refine

# create a router instance for this file
router = APIRouter(prefix="/demo")


def _get_demo_zip_path() -> Path:
    """
    Get the path to the demo ZIP file.
    """

    return file_io.get_asset_path("demo", "monmothma.zip")


def _get_file_size_difference_percentage(
    unrefined_document: str, refined_document: str
) -> int:
    unrefined_bytes = len(unrefined_document.encode("utf-8"))
    refined_bytes = len(refined_document.encode("utf-8"))

    if unrefined_bytes == 0:
        return 0

    percent_diff = (unrefined_bytes - refined_bytes) / unrefined_bytes * 100
    return round(percent_diff)


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
                }
            )
        )
    except XMLValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "details": e.details},
        )


@router.get("/download")
async def demo_download(file_path: Path = Depends(_get_demo_zip_path)) -> FileResponse:
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

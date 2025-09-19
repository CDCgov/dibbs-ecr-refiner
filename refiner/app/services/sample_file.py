import io
from pathlib import Path

from fastapi import UploadFile
from fastapi.datastructures import Headers

from .file_io import get_asset_path


def get_sample_zip_path() -> Path:
    """
    Get the path to the demo zip file provided by the application.
    """

    return get_asset_path("demo", "mon-mothma-two-conditions.zip")


def create_sample_zip_file(sample_zip_path: Path) -> UploadFile:
    """
    Given a path to a sample file, packages the file as an UploadFile to use for processing.

    Args:
        sample_zip_path (Path): Path to file

    Returns:
        UploadFile: The file packaged as an UploadFile
    """

    # Expected asset path
    asset_root = get_asset_path("demo").resolve()

    # Check that sample zip path is within expected asset path
    fullpath = sample_zip_path.resolve()
    if not str(fullpath).startswith(str(asset_root)):
        raise ValueError("Attempt to access file outside allowed asset directory.")

    filename = sample_zip_path.name
    with open(sample_zip_path, "rb") as demo_file:
        zip_content = demo_file.read()

    file_like = io.BytesIO(zip_content)
    file_like.seek(0)
    file = UploadFile(
        file=file_like,
        filename=filename,
        headers=Headers({"Content-Type": "application/zip"}),
    )
    return file

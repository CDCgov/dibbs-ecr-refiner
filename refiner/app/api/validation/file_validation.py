from logging import Logger
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from app.core.models.types import XMLFiles
from app.services import file_io
from app.services.sample_file import create_sample_zip_file

# File uploads
MAX_ALLOWED_UPLOAD_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ALLOWED_UNCOMPRESSED_FILE_SIZE = MAX_ALLOWED_UPLOAD_FILE_SIZE * 5  # 50 MB


async def get_validated_xml_files(file: UploadFile, logger: Logger) -> XMLFiles:
    """
    Returns a fully validated XMLFiles object. Throws an exception if validation fails.

    Args:
        file (UploadFile): The uploaded file
        logger (Logger): The logger

    Raises:
        HTTPException: 400 if a ZIP validation error occurs
        HTTPException: 400 if an XML processing error occurs
        HTTPException: 400 if a generic file processing error occurs

    Returns:
        XMLFiles: Fully validated XMLFiles object
    """
    try:
        return await file_io.read_xml_zip(file)
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


def validate_path_or_raise(path: Path) -> None:
    """
    Throws an HTTPException if the path can't be found.

    Args:
        path (Path): The path to validate

    Raises:
        HTTPException: 404 if zip file path can't be found
    """
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )


async def get_validated_file(
    uploaded_file: UploadFile | None, demo_file_path: Path, logger: Logger
) -> UploadFile:
    """
    Returns a validated file to use for the test flow.

    Args:
        uploaded_file (UploadFile | None): The uploaded file object
        demo_file_path (Path): The path to the demo file
        logger (Logger): The logger

    Raises:
        HTTPException: 400 if zip processing fails

    Returns:
        UploadFile: A validated file object
    """
    if not uploaded_file:
        return create_sample_zip_file(sample_zip_path=demo_file_path)

    try:
        return await _validate_zip_file(file=uploaded_file)
    except ZipValidationError as e:
        logger.error(
            msg="ZipValidationError in validate_zip_file",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )


async def _validate_zip_file(file: UploadFile) -> UploadFile:
    """
    Validate an uploaded eICR/RR pair packaged in a zip file. Ensure it meets criteria necessary for processing.

    Args:
        file (UploadFile): eICR/RR pair as a .zip

    Raises:
        HTTPException: 400 if not a .zip
        HTTPException: 400 if file names begins with "."
        HTTPException: 400 if file name contains multiple periods in a row, ".."
        HTTPException: 400 if .zip is empty
        HTTPException: 400 if file is larger than `MAX_ALLOWED_UPLOAD_FILE_SIZE`

    Returns:
        UploadFile: The validated .zip file
    """
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

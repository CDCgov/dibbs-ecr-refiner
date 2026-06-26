from logging import Logger
from pathlib import Path
from typing import Literal, get_args

from fastapi import HTTPException, UploadFile, status
from lxml import etree

from app.core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipSizeError,
    ZipValidationError,
)
from app.core.models.types import XMLFiles
from app.services import file_io
from app.services.format import format_xml_document_for_display
from app.services.sample_file import create_sample_zip_file

# File uploads
MEGABYTES = 1024 * 1024

# defining these type literals to get Orval to pick them up and codegen them to the frontend
DiffMax = Literal[2]
UncompressedMax = Literal[15]

DIFF_RENDERING_MAX_MB = get_args(DiffMax)[0]
UNCOMPRESSED_MAX_MB = get_args(UncompressedMax)[0]

DIFF_RENDERING_MAX_BYTES = DIFF_RENDERING_MAX_MB * MEGABYTES
UNCOMPRESSED_MAX_BYTES = UNCOMPRESSED_MAX_MB * MEGABYTES


def format_xml_document_for_display_or_raise(text: str) -> str:
    """
    Formats XML for display purposes. Raises a 422 if the input is not valid XML.
    """
    try:
        return format_xml_document_for_display(text)
    except etree.XMLSyntaxError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid XML: {e.msg} (line {e.lineno}, column {e.offset})",
        )


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
    except ZipSizeError as e:
        logger.error("ZipSizeError in read_xml_zip", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ZIP archive is too large. Please upload a file that's less than {UNCOMPRESSED_MAX_MB}MB in size",
        )
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
    uploaded_file: UploadFile | None, test_file_path: Path, logger: Logger
) -> UploadFile:
    """
    Returns a validated file to use for the simulator and inline testing flow.

    Args:
        uploaded_file (UploadFile | None): The uploaded file object
        test_file_path (Path): The path to the test file
        logger (Logger): The logger

    Raises:
        HTTPException: 400 if zip processing fails

    Returns:
        UploadFile: A validated file object
    """
    if not uploaded_file:
        return create_sample_zip_file(sample_zip_path=test_file_path)

    try:
        return await _validate_ecr_zip_pair(file=uploaded_file)
    except ZipValidationError as e:
        logger.error(
            msg="ZipValidationError in validate_zip_file",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive cannot be read. CDA_eICR.xml and CDA_RR.xml files must be present.",
        )


async def _validate_ecr_zip_pair(file: UploadFile) -> UploadFile:
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
    if file.size > UNCOMPRESSED_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uncompressed file must be less than {UNCOMPRESSED_MAX_MB}MB in size.",
        )

    return file

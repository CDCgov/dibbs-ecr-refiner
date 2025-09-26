from fastapi import HTTPException, UploadFile, status

# File uploads
MAX_ALLOWED_UPLOAD_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ALLOWED_UNCOMPRESSED_FILE_SIZE = MAX_ALLOWED_UPLOAD_FILE_SIZE * 5  # 50 MB


async def validate_zip_file(file: UploadFile) -> UploadFile:
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

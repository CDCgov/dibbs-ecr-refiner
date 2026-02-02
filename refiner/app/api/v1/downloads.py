from logging import Logger
from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ...db.users.model import DbUser
from ...services.aws.s3 import S3_CONFIGURATION_BUCKET_NAME, s3_client
from ...services.logger import get_logger
from ..auth.middleware import get_logged_in_user

router = APIRouter(prefix="/downloads")


def _parse_user_id_from_key(key: str) -> UUID | None:
    """
    Extract the user_id from an S3 key.

    Expected key format: refiner-test-suite/{date}/{user_id}/{filename}

    Args:
        key: The S3 key to parse

    Returns:
        The user_id as a UUID, or None if parsing fails
    """
    try:
        parts = key.split("/")
        if len(parts) >= 4 and parts[0] == "refiner-test-suite":
            return UUID(parts[2])
    except (ValueError, IndexError):
        pass
    return None


def _get_filename_from_key(key: str) -> str:
    """
    Extract the filename from an S3 key.

    Args:
        key: The S3 key to parse

    Returns:
        The filename portion of the key
    """
    return key.split("/")[-1] if "/" in key else key


@router.get(
    "/{key:path}",
    tags=["downloads"],
    operation_id="downloadRefinedEcr",
)
async def download_refined_ecr(
    key: str,
    user: DbUser = Depends(get_logged_in_user),
    logger: Logger = Depends(get_logger),
) -> StreamingResponse:
    """
    Download a refined eCR ZIP file from S3.

    Validates that the authenticated user owns the file before streaming it back.

    Args:
        key: The S3 key of the file to download
        user: The authenticated user making the request
        logger: The application logger

    Returns:
        StreamingResponse: The file streamed from S3

    Raises:
        HTTPException: 403 if user doesn't own the file, 404 if file not found
    """
    # Validate user ownership
    key_user_id = _parse_user_id_from_key(key)
    if key_user_id is None or key_user_id != user.id:
        logger.warning(
            "Unauthorized download attempt",
            extra={
                "key": key,
                "key_user_id": str(key_user_id) if key_user_id else None,
                "requesting_user_id": str(user.id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download this file.",
        )

    # Fetch file from S3
    try:
        s3_response = s3_client.get_object(
            Bucket=S3_CONFIGURATION_BUCKET_NAME,
            Key=key,
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("NoSuchKey", "404"):
            logger.warning(
                "Download requested for non-existent S3 key",
                extra={"key": key, "user_id": str(user.id)},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )
        logger.error(
            "S3 error during file download",
            extra={"key": key, "user_id": str(user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the file.",
        )

    filename = _get_filename_from_key(key)

    # "filename" is a built-in attribute on LogRecord (module filename).
    # Passing it in `extra` causes `logging` to raise KeyError: "Attempt to overwrite 'filename' in LogRecord".
    # Use a non-conflicting key name for the download filename.
    logger.info(
        "Streaming file download",
        extra={"key": key, "user_id": str(user.id), "download_filename": filename},
    )

    return StreamingResponse(
        content=s3_response["Body"].iter_chunks(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )

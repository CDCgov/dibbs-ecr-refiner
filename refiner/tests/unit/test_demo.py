import io
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.datastructures import Headers

from app.api.validation.file_validation import (
    MAX_ALLOWED_UPLOAD_FILE_SIZE,
    validate_zip_file,
)
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import create_refined_ecr_zip_in_memory

api_route_base = "/api/v1/demo"


@pytest.mark.asyncio
async def test_demo_file_not_found(authed_client, test_app, mock_logged_in_user):
    from app.services.sample_file import get_sample_zip_path

    def mock_missing_path() -> Path:
        return Path("/nonexistent/demo.zip")

    test_app.dependency_overrides[get_sample_zip_path] = mock_missing_path

    response = await authed_client.post(f"{api_route_base}/upload")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unable to find demo zip file to download."}

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_route_s3_failure(test_app, authed_client):
    from app.services.aws.s3 import upload_refined_ecr

    def fake_upload_refined_ecr():
        return ""

    test_app.dependency_overrides[upload_refined_ecr] = lambda: fake_upload_refined_ecr

    response = await authed_client.post(f"{api_route_base}/upload")

    assert response.status_code == 200
    assert "refined_download_key" in response.json()
    assert response.json()["refined_download_key"] == ""

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_valid_zip():
    zip_bytes = create_zip_file(
        {"CDA_eICR.xml": b"<xml>eICR</xml>", "CDA_RR.xml": b"<xml>RR</xml>"}
    )
    file = create_mock_upload_file("valid.zip", zip_bytes)
    validated = await validate_zip_file(file)
    assert validated is file


@pytest.mark.asyncio
async def test_invalid_extension():
    zip_bytes = create_zip_file({"test.txt": b"abc"})
    file = create_mock_upload_file("invalid.txt", zip_bytes)
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "Only .zip files are allowed" in exc.value.detail


@pytest.mark.asyncio
async def test_filename_starts_with_period():
    file = create_mock_upload_file(".hidden.zip", b"fake")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "cannot start with a period" in exc.value.detail


@pytest.mark.asyncio
async def test_filename_with_double_dot():
    file = create_mock_upload_file("bad..name.zip", b"fake")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "cannot contain multiple periods" in exc.value.detail


@pytest.mark.asyncio
async def test_empty_file():
    file = create_mock_upload_file("empty.zip", b"")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert ".zip must not be empty" in exc.value.detail


@pytest.mark.asyncio
async def test_file_too_large():
    content = b"x" * (MAX_ALLOWED_UPLOAD_FILE_SIZE + 1)
    file = create_mock_upload_file("big.zip", content)
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "must be less than 10MB" in exc.value.detail


@pytest.mark.parametrize(
    "unrefined, refined, expected",
    [
        pytest.param("this is a test", "this is a test", 0, id="same_doc"),  # Same doc
        pytest.param("", "", 0, id="empty_doc"),  # Empty docs
        pytest.param(
            "A" * 20_000, "A" * 10_000, 50, id="50_percent_reduction"
        ),  # 50% reduction
    ],
)
def test_file_size_difference_percentage(
    unrefined: str, refined: str, expected: int
) -> None:
    result = get_file_size_reduction_percentage(unrefined, refined)
    assert result == expected


def create_mock_upload_file(
    filename: str,
    content: bytes,
) -> UploadFile:
    file_like = io.BytesIO(content)
    upload = UploadFile(
        file=file_like,
        filename=filename,
        headers=Headers({"Content-Type": "application/zip"}),
    )

    upload.size = len(content)
    return upload


def create_zip_file(file_dict: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in file_dict.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_create_refined_ecr_zip():
    refined_files = [
        ("covid_condition.xml", "<eICR>Covid Data</eICR>"),
        ("flu_condition.xml", "<eICR>Flu Data</eICR>"),
    ]

    eicr = "<eICR>Some RR Data</eICR>"

    refined_files.append(("CDA_eICR.xml", eicr))

    file_name, file_buffer = create_refined_ecr_zip_in_memory(files=refined_files)

    assert "_refined_ecr.zip" in file_name

    with zipfile.ZipFile(file_buffer, "r") as zipf:
        namelist = zipf.namelist()
        assert "covid_condition.xml" in namelist
        assert "flu_condition.xml" in namelist
        assert "CDA_eICR.xml" in namelist

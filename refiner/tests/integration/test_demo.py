import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.datastructures import Headers
from fastapi.testclient import TestClient

from app.api.auth.middleware import get_logged_in_user
from app.api.validation.file_validation import (
    MAX_ALLOWED_UPLOAD_FILE_SIZE,
    validate_zip_file,
)
from app.db.users.model import DbUser
from app.main import app
from app.services.ecr.refine import get_file_size_reduction_percentage
from app.services.file_io import create_refined_ecr_zip_in_memory

api_route_base = "/api/v1/demo"

client = TestClient(app=app)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_demo_upload_smoke(
    covid_influenza_v1_1_zip_path: Path, authed_client
) -> None:
    """
    Smoke test for the /api/v1/demo/upload endpoint.
    Verifies that the endpoint processes a demo ZIP file and returns a 200 with expected top-level fields.
    """

    uploaded_file = covid_influenza_v1_1_zip_path
    with open(uploaded_file, "rb") as file_data:
        response = await authed_client.post(
            f"{api_route_base}/upload",
            files={
                "uploaded_file": (
                    "mon_mothma_covid_influenza_1.1.zip",
                    file_data,
                    "application/zip",
                )
            },
        )
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert "refined_conditions" in data
    assert "conditions_without_matching_configs" in data
    assert "unrefined_eicr" in data
    assert "refined_download_url" in data


def test_upload_route_s3_failure(test_user_id, test_username, monkeypatch):
    from app.services.aws.s3 import upload_refined_ecr

    def fake_upload_refined_ecr(user_id, file_buffer, filename, expires=3600):
        return ""

    def mock_get_logged_in_user():
        from datetime import datetime

        from app.db.users.model import DbUser

        return DbUser(
            id=test_user_id,
            username=test_username,
            email="test@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    app.dependency_overrides[upload_refined_ecr] = lambda: fake_upload_refined_ecr
    app.dependency_overrides[get_logged_in_user] = mock_get_logged_in_user

    client = TestClient(app)

    response = client.post(f"{api_route_base}/upload")

    assert response.status_code == 200
    assert "refined_download_url" in response.json()
    assert response.json()["refined_download_url"] == ""

    app.dependency_overrides.clear()


@pytest.mark.integration
def test_demo_file_not_found(test_user_id, test_username):
    from app.services.sample_file import get_sample_zip_path

    def mock_missing_path() -> Path:
        return Path("/nonexistent/demo.zip")

    def mock_get_logged_in_user():
        return DbUser(
            id=test_user_id,
            username=test_username,
            email="test@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    app.dependency_overrides[get_sample_zip_path] = mock_missing_path
    app.dependency_overrides[get_logged_in_user] = mock_get_logged_in_user

    response = client.post(f"{api_route_base}/upload")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unable to find demo zip file to download."}

    response = client.get(f"{api_route_base}/download")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unable to find demo zip file to download."}

    app.dependency_overrides.clear()


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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_valid_zip():
    zip_bytes = create_zip_file(
        {"CDA_eICR.xml": b"<xml>eICR</xml>", "CDA_RR.xml": b"<xml>RR</xml>"}
    )
    file = create_mock_upload_file("valid.zip", zip_bytes)
    validated = await validate_zip_file(file)
    assert validated is file


@pytest.mark.asyncio
@pytest.mark.integration
async def test_invalid_extension():
    zip_bytes = create_zip_file({"test.txt": b"abc"})
    file = create_mock_upload_file("invalid.txt", zip_bytes)
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "Only .zip files are allowed" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_filename_starts_with_period():
    file = create_mock_upload_file(".hidden.zip", b"fake")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "cannot start with a period" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_filename_with_double_dot():
    file = create_mock_upload_file("bad..name.zip", b"fake")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "cannot contain multiple periods" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_empty_file():
    file = create_mock_upload_file("empty.zip", b"")
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert ".zip must not be empty" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.integration
async def test_file_too_large():
    content = b"x" * (MAX_ALLOWED_UPLOAD_FILE_SIZE + 1)
    file = create_mock_upload_file("big.zip", content)
    with pytest.raises(HTTPException) as exc:
        await validate_zip_file(file)
    assert "must be less than 10MB" in exc.value.detail


@pytest.mark.parametrize(
    "unrefined, refined, expected",
    [
        ("this is a test", "this is a test", 0),  # Same doc
        ("", "", 0),  # Empty docs
        ("A" * 20_000, "A" * 10_000, 50),  # 50% reduction
    ],
)
def test_file_size_difference_percentage(
    unrefined: str, refined: str, expected: int
) -> None:
    result = get_file_size_reduction_percentage(unrefined, refined)
    assert result == expected


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

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
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


@pytest.fixture
def mock_user():
    return DbUser(
        id=uuid4(),
        username="mockuser",
        email="mockuser@test.com",
        jurisdiction_id="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


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
    assert "refined_download_key" in data


def test_upload_route_s3_failure(test_user_id, test_username, monkeypatch):
    from app.services.aws.s3 import upload_refined_ecr

    def fake_upload_refined_ecr(user_id, file_buffer, filename, logger):
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
    assert "refined_download_key" in response.json()
    assert response.json()["refined_download_key"] == ""

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
        ("covid_condition.xml", b"<eICR>Covid Data</eICR>"),
        ("flu_condition.xml", b"<eICR>Flu Data</eICR>"),
    ]

    eicr = b"<eICR>Some RR Data</eICR>"

    refined_files.append(("CDA_eICR.xml", eicr))

    file_name, file_buffer = create_refined_ecr_zip_in_memory(files=refined_files)

    assert "_refined_ecr.zip" in file_name

    with zipfile.ZipFile(file_buffer, "r") as zipf:
        namelist = zipf.namelist()
        assert "covid_condition.xml" in namelist
        assert "flu_condition.xml" in namelist
        assert "CDA_eICR.xml" in namelist


api_route_base_downloads = "/api/v1/demo/download"


def create_mock_s3_response(content: bytes = b"mock zip content"):
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = iter([content])
    return {"Body": mock_body}


class TestDownloadRefinedEcr:
    def test_successful_download(self):
        from app.db.users.model import DbUser

        user = DbUser(
            id=uuid4(),
            username="tester",
            email="test1@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.dependency_overrides[get_logged_in_user] = lambda: user
        filename = "test-file.zip"
        with (
            patch("app.services.aws.s3.fetch_zip_from_s3") as mock_fetch_zip_from_s3,
            patch(
                "app.services.aws.s3.find_user_file_key_by_filename"
            ) as mock_find_key,
        ):
            mock_fetch_zip_from_s3.return_value = create_mock_s3_response()
            mock_find_key.return_value = (
                f"refiner-test-suite/2026-01-29/{user.id}/{filename}"
            )
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
            assert (
                response.headers["content-disposition"]
                == 'attachment; filename="test-file.zip"'
            )
            assert response.content == b"mock zip content"
            mock_fetch_zip_from_s3.assert_called_once()
            mock_find_key.assert_called_once_with(user.id, filename, ANY)
        app.dependency_overrides.clear()

    def test_download_file_not_found_for_user(self):
        from app.db.users.model import DbUser

        user = DbUser(
            id=uuid4(),
            username="tester404",
            email="test404@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.dependency_overrides[get_logged_in_user] = lambda: user
        filename = "nonexistent.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = None
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_download_s3_internal_error(self):
        from app.db.users.model import DbUser

        user = DbUser(
            id=uuid4(),
            username="tester500",
            email="test500@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.dependency_overrides[get_logged_in_user] = lambda: user
        filename = "somefile.zip"
        with (
            patch(
                "app.services.aws.s3.find_user_file_key_by_filename"
            ) as mock_find_key,
            patch("app.services.aws.s3.fetch_zip_from_s3") as mock_fetch_zip_from_s3,
        ):
            mock_find_key.return_value = (
                f"refiner-test-suite/2022-12-24/{user.id}/{filename}"
            )
            from botocore.exceptions import ClientError

            mock_fetch_zip_from_s3.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "Internal error"}},
                "GetObject",
            )
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 500
        app.dependency_overrides.clear()

    def test_requires_authentication(self):
        filename = "unauth.zip"
        client = TestClient(app)
        response = client.get(f"{api_route_base_downloads}/{filename}")
        assert response.status_code == 401

    def test_forbidden_when_user_doesnt_own_file(self):
        from app.db.users.model import DbUser

        user = DbUser(
            id=uuid4(),
            username="tester",
            email="test1@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        DbUser(
            id=uuid4(),
            username="hacker",
            email="test2@test.com",
            jurisdiction_id="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.dependency_overrides[get_logged_in_user] = lambda: user
        filename = "other-file.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = None
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 404
        app.dependency_overrides.clear()

    def test_forbidden_when_key_has_invalid_user_id(self, mock_user):
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user
        filename = "file.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = None
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 404
            assert response.json() == {"detail": "File not found."}
        app.dependency_overrides.clear()

    def test_forbidden_when_key_has_wrong_format(self, mock_user):
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user
        filename = "file.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = None
            client = TestClient(app)
            response = client.get(f"{api_route_base_downloads}/{filename}")
            assert response.status_code == 404
            assert response.json() == {"detail": "File not found."}
        app.dependency_overrides.clear()

    def test_not_found_when_s3_key_doesnt_exist(self, mock_user):
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user
        filename = "nonexistent.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = (
                f"refiner-test-suite/2026-01-29/{mock_user.id}/nonexistent.zip"
            )
            with patch(
                "app.services.aws.s3.fetch_zip_from_s3"
            ) as mock_fetch_zip_from_s3:
                mock_fetch_zip_from_s3.side_effect = ClientError(
                    {
                        "Error": {
                            "Code": "NoSuchKey",
                            "Message": "The specified key does not exist.",
                        }
                    },
                    "GetObject",
                )
                client = TestClient(app)
                response = client.get(f"{api_route_base_downloads}/{filename}")
                assert response.status_code == 404
                assert response.json() == {"detail": "File not found."}
        app.dependency_overrides.clear()

    def test_server_error_on_s3_failure(self, mock_user):
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user
        filename = "file.zip"
        with patch(
            "app.services.aws.s3.find_user_file_key_by_filename"
        ) as mock_find_key:
            mock_find_key.return_value = (
                f"refiner-test-suite/2026-01-29/{mock_user.id}/file.zip"
            )
            with patch(
                "app.services.aws.s3.fetch_zip_from_s3"
            ) as mock_fetch_zip_from_s3:
                mock_fetch_zip_from_s3.side_effect = ClientError(
                    {"Error": {"Code": "InternalError", "Message": "Internal error"}},
                    "GetObject",
                )
                client = TestClient(app)
                response = client.get(f"{api_route_base_downloads}/{filename}")
                assert response.status_code == 500
                assert response.json() == {
                    "detail": "An error occurred while retrieving the file."
                }
        app.dependency_overrides.clear()

    def test_requires_authentication_for_s3_key(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        filename = "file.zip"
        response = client.get(f"{api_route_base_downloads}/{filename}")
        assert response.status_code == 401


class TestGetFilenameFromKey:
    def test_extracts_filename(self):
        from app.api.v1.demo import _get_filename_from_key

        key = "refiner-test-suite/2026-01-29/user-id/my-refined-ecr.zip"
        result = _get_filename_from_key(key)
        assert result == "my-refined-ecr.zip"

    def test_handles_key_without_slashes(self):
        from app.api.v1.demo import _get_filename_from_key

        key = "just-a-filename.zip"
        result = _get_filename_from_key(key)
        assert result == "just-a-filename.zip"

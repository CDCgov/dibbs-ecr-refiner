import io
import pathlib
import zipfile
from typing import Any

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.datastructures import Headers
from fastapi.testclient import TestClient

from app.api.auth.middleware import get_logged_in_user
from app.api.v1.demo import (
    MAX_ALLOWED_UPLOAD_FILE_SIZE,
    _create_refined_ecr_zip_in_memory,
    _get_file_size_difference_percentage,
    _validate_zip_file,
)
from app.main import app

api_route_base = "/api/v1/demo"

client = TestClient(app=app)


@pytest.mark.integration
class TestDemo:
    @pytest.mark.asyncio
    async def test_demo_upload_success(
        self, test_assets_path: pathlib.Path, authed_client
    ) -> None:
        """
        Test successful demo file upload and processing
        """

        uploaded_file = test_assets_path / "demo" / "monmothma.zip"
        with open(uploaded_file, "rb") as file_data:
            response = await authed_client.post(
                f"{api_route_base}/upload",
                files={
                    "uploaded_file": ("monmothma.zip", file_data, "application/zip")
                },
            )
        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert "conditions" in data
        assert "unrefined_eicr" in data
        assert "refined_download_url" in data
        assert "test-user" in data["refined_download_url"]
        assert "/refiner-app/refiner-test-suite/" in data["refined_download_url"]
        assert "stats" in data["conditions"][0]
        assert any(
            "file size reduced by" in stat for stat in data["conditions"][0]["stats"]
        )

    def test_demo_file_not_found(self) -> None:
        """
        Test error handling when demo file is missing
        """

        from app.api.v1.demo import _get_demo_zip_path  # Import the actual function

        def mock_missing_path() -> pathlib.Path:
            return pathlib.Path("/nonexistent/demo.zip")

        def mock_get_logged_in_user():
            return {"id": "test-user", "username": "test-user"}

        # use the actual function reference, not a string
        app.dependency_overrides[_get_demo_zip_path] = mock_missing_path
        app.dependency_overrides[get_logged_in_user] = mock_get_logged_in_user

        # test both endpoints with missing file
        response = client.post(f"{api_route_base}/upload")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

        response = client.get(f"{api_route_base}/download")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

        app.dependency_overrides.clear()

    def create_mock_upload_file(
        self,
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

    def create_zip_file(self, file_dict: dict[str, bytes]) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, content in file_dict.items():
                z.writestr(name, content)
        return buf.getvalue()

    @pytest.mark.asyncio
    async def test_valid_zip(self):
        zip_bytes = self.create_zip_file(
            {"CDA_eICR.xml": b"<xml>eICR</xml>", "CDA_RR.xml": b"<xml>RR</xml>"}
        )
        file = self.create_mock_upload_file("valid.zip", zip_bytes)
        validated = await _validate_zip_file(file)
        assert validated is file

    @pytest.mark.asyncio
    async def test_invalid_extension(self):
        zip_bytes = self.create_zip_file({"test.txt": b"abc"})
        file = self.create_mock_upload_file("invalid.txt", zip_bytes)
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "Only .zip files are allowed" in exc.value.detail

    @pytest.mark.asyncio
    async def test_filename_starts_with_period(self):
        file = self.create_mock_upload_file(".hidden.zip", b"fake")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "cannot start with a period" in exc.value.detail

    @pytest.mark.asyncio
    async def test_filename_with_double_dot(self):
        file = self.create_mock_upload_file("bad..name.zip", b"fake")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "cannot contain multiple periods" in exc.value.detail

    @pytest.mark.asyncio
    async def test_empty_file(self):
        file = self.create_mock_upload_file("empty.zip", b"")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert ".zip must not be empty" in exc.value.detail

    @pytest.mark.asyncio
    async def test_file_too_large(self):
        content = b"x" * (MAX_ALLOWED_UPLOAD_FILE_SIZE + 1)
        file = self.create_mock_upload_file("big.zip", content)
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
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
    """
    Test the file size difference calculation function
    """

    result = _get_file_size_difference_percentage(unrefined, refined)
    assert result == expected


def test_create_refined_ecr_zip():
    # Simulated refined files
    refined_files = [
        ("covid_condition.xml", "<eICR>Covid Data</eICR>"),
        ("flu_condition.xml", "<eICR>Flu Data</eICR>"),
    ]

    # Simulated eICR XML
    eicr = "<eICR>Some RR Data</eICR>"

    refined_files.append(("CDA_eICR.xml", eicr))

    file_name, file_buffer = _create_refined_ecr_zip_in_memory(files=refined_files)

    assert "_refined_ecr.zip" in file_name

    with zipfile.ZipFile(file_buffer, "r") as zipf:
        namelist = zipf.namelist()
        assert "covid_condition.xml" in namelist
        assert "flu_condition.xml" in namelist
        assert "CDA_eICR.xml" in namelist

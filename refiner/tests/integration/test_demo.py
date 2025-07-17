import asyncio
import io
import pathlib
import time
import zipfile
from typing import Any

import pytest
from fastapi import HTTPException, Response, UploadFile
from fastapi.datastructures import Headers

from app.api.v1.demo import (
    MAX_ALLOWED_UPLOAD_FILE_SIZE,
    _cleanup_expired_files,
    _create_refined_ecr_zip,
    _create_zipfile_output_directory,
    _get_file_size_difference_percentage,
    _update_file_store,
    _validate_zip_file,
    file_store,
)
from app.main import app

api_route_base = "/api/v1/demo"


@pytest.mark.asyncio
async def test_cleanup_expired_files(tmp_path):
    async def _run_cleanup_once():
        await asyncio.to_thread(_cleanup_expired_files)

    old_file = tmp_path / "should_be_deleted.txt"
    old_file.write_text("outdated")
    file_store.clear()

    file_store["delete"] = {
        "path": str(old_file),
        "timestamp": time.time() - 180,  # expired
    }

    await _run_cleanup_once()

    assert "delete" not in file_store
    assert not old_file.exists()


@pytest.mark.asyncio
@pytest.mark.integration
class DemoTests:
    def test_create_refined_ecr_zip(tmp_path):
        # Simulated refined files
        refined_files = [
            ("covid_condition.xml", "<eICR>Covid Data</eICR>"),
            ("flu_condition.xml", "<eICR>Flu Data</eICR>"),
        ]

        # Simulated eICR XML
        eicr = "<eICR>Some RR Data</eICR>"

        refined_files.append(("CDA_eICR.xml", eicr))

        file_name, file_path, token = _create_refined_ecr_zip(
            files=refined_files, output_dir=tmp_path
        )

        assert file_name == f"{token}_refined_ecr.zip"
        assert pathlib.Path(file_path).exists()

        with zipfile.ZipFile(file_path, "r") as zipf:
            namelist = zipf.namelist()
            assert "covid_condition.xml" in namelist
            assert "flu_condition.xml" in namelist
            assert "CDA_eICR.xml" in namelist

    def test_get_processed_ecr_directory(tmp_path):
        result = _create_zipfile_output_directory(tmp_path / "refined-ecr")

        assert result.exists()
        assert result.name == "refined-ecr"
        assert result.parent == tmp_path

    def test_update_file_store():
        # Setup for testing
        file_store.clear()
        filename = "report.zip"
        path = pathlib.Path("tmp") / filename
        token = "example-token"

        before = time.time()
        _update_file_store(filename, path, token)
        after = time.time()

        entry = file_store[token]

        # Check expected attributes in the dict
        assert entry["filename"] == filename
        assert entry["path"] == path

        # Ensure timestamp is in the middle
        assert before <= entry["timestamp"] <= after

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

    async def test_demo_upload_success(
        test_assets_path: pathlib.Path, authed_client
    ) -> None:
        """
        Test successful demo file upload and processing
        """

        from app.api.v1.demo import (
            _get_demo_zip_path,
            _get_refined_ecr_output_dir,
            _get_zip_creator,
        )

        def mock_path_dep():
            return test_assets_path / "demo" / "monmothma.zip"

        def mock_zip_creator():
            def _mock_create_zip(*, files, output_dir):
                return (
                    "mocked_output.zip",
                    pathlib.Path("/tmp/mocked_output.zip"),
                    "mocked_token",
                )

            return _mock_create_zip

        def mock_output_dir():
            return "/tmp"

        # Use the actual function reference, not a string
        app.dependency_overrides[_get_refined_ecr_output_dir] = mock_output_dir
        app.dependency_overrides[_get_demo_zip_path] = mock_path_dep
        app.dependency_overrides[_get_zip_creator] = mock_zip_creator
        # Mock the file store to avoid actual file system changes
        response = await authed_client.post(f"{api_route_base}/upload")
        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert "conditions" in data
        assert "unrefined_eicr" in data
        assert "refined_download_token" in data
        assert "stats" in data["conditions"][0]
        assert any(
            "file size reduced by" in stat for stat in data["conditions"][0]["stats"]
        )

        app.dependency_overrides.clear()

    async def test_demo_download_success(
        test_assets_path: pathlib.Path, authed_client
    ) -> None:
        """
        Test successful demo file download
        """

        from app.api.v1.demo import _get_demo_zip_path

        def mock_path_dep() -> pathlib.Path:
            return test_assets_path / "demo" / "monmothma.zip"

        # Use the actual function reference, not a string
        app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

        response: Response = await authed_client.get(f"{api_route_base}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "monmothma.zip" in response.headers["content-disposition"]

        app.dependency_overrides.clear()

    async def test_demo_file_not_found(authed_client) -> None:
        """
        Test error handling when demo file is missing
        """

        from app.api.v1.demo import _get_demo_zip_path  # Import the actual function

        def mock_missing_path() -> pathlib.Path:
            return pathlib.Path("/nonexistent/demo.zip")

        # use the actual function reference, not a string
        app.dependency_overrides[_get_demo_zip_path] = mock_missing_path

        # test both endpoints with missing file
        response = await authed_client.post(f"{api_route_base}/upload")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

        response = await authed_client.get(f"{api_route_base}/download")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

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

    async def test_valid_zip(self):
        zip_bytes = self.create_zip_file(
            {"CDA_eICR.xml": b"<xml>eICR</xml>", "CDA_RR.xml": b"<xml>RR</xml>"}
        )
        file = self.create_mock_upload_file("valid.zip", zip_bytes)
        validated = await _validate_zip_file(file)
        assert validated is file

    async def test_invalid_extension(self):
        zip_bytes = self.create_zip_file({"test.txt": b"abc"})
        file = self.create_mock_upload_file("invalid.txt", zip_bytes)
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "Only .zip files are allowed" in exc.value.detail

    async def test_filename_starts_with_period(self):
        file = self.create_mock_upload_file(".hidden.zip", b"fake")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "cannot start with a period" in exc.value.detail

    async def test_filename_with_double_dot(self):
        file = self.create_mock_upload_file("bad..name.zip", b"fake")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "cannot contain multiple periods" in exc.value.detail

    async def test_empty_file(self):
        file = self.create_mock_upload_file("empty.zip", b"")
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert ".zip must not be empty" in exc.value.detail

    async def test_file_too_large(self):
        content = b"x" * (MAX_ALLOWED_UPLOAD_FILE_SIZE + 1)
        file = self.create_mock_upload_file("big.zip", content)
        with pytest.raises(HTTPException) as exc:
            await _validate_zip_file(file)
        assert "must be less than 10MB" in exc.value.detail

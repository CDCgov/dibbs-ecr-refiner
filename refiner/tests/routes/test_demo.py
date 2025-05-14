import asyncio
import os
import pathlib
import time
from typing import Any

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.api.v1.demo import (
    _cleanup_expired_files,
    _create_refined_ecr_zip,
    _get_file_size_difference_percentage,
    _get_processed_ecr_directory,
    _update_file_store,
    file_store,
)
from app.main import app

client = TestClient(app)

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


def test_create_refined_ecr_zip(tmp_path):
    file_name, file_path, token = _create_refined_ecr_zip(
        "<eICR>", "<RR>", output_dir=tmp_path
    )
    assert file_name == f"{token}_refined_ecr.zip"
    assert pathlib.Path(file_path).exists()
    os.remove(file_path)


def test_get_processed_ecr_directory(tmp_path):
    result = _get_processed_ecr_directory(tmp_path / "refined-ecr")

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


def test_demo_upload_success(test_assets_path: pathlib.Path) -> None:
    """
    Test successful demo file upload and processing
    """

    from app.api.v1.demo import _get_demo_zip_path, get_zip_creator

    def mock_path_dep() -> pathlib.Path:
        return test_assets_path / "demo" / "monmothma.zip"

    def mock_zip_creator():
        return lambda refined, unrefined, path: ("fake", pathlib.Path("fake"), "fake")

    # Use the actual function reference, not a string
    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep
    app.dependency_overrides[get_zip_creator] = mock_zip_creator

    response = client.get(f"{api_route_base}/upload")
    assert response.status_code == 200

    data: dict[str, Any] = response.json()
    assert "unrefined_eicr" in data
    assert "refined_eicr" in data
    assert "reportable_conditions" in data
    assert "stats" in data
    assert any("file size reduced by" in stat for stat in data["stats"])

    app.dependency_overrides.clear()


def test_demo_download_success(test_assets_path: pathlib.Path) -> None:
    """
    Test successful demo file download
    """

    from app.api.v1.demo import _get_demo_zip_path

    def mock_path_dep() -> pathlib.Path:
        return test_assets_path / "demo" / "monmothma.zip"

    # Use the actual function reference, not a string
    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

    response: Response = client.get(f"{api_route_base}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "monmothma.zip" in response.headers["content-disposition"]

    app.dependency_overrides.clear()


def test_demo_file_not_found() -> None:
    """
    Test error handling when demo file is missing
    """

    from app.api.v1.demo import _get_demo_zip_path  # Import the actual function

    def mock_missing_path() -> pathlib.Path:
        return pathlib.Path("/nonexistent/demo.zip")

    # use the actual function reference, not a string
    app.dependency_overrides[_get_demo_zip_path] = mock_missing_path

    # test both endpoints with missing file
    for endpoint in ["upload", "download"]:
        response = client.get(f"{api_route_base}/{endpoint}")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

    app.dependency_overrides.clear()

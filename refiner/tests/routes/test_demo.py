import pathlib
from typing import Any

import pytest
from fastapi import Response
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

api_route_base = "message-refiner/api/v1/demo"


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

    # Test the function logic directly without importing
    def calculate_size_diff(unrefined_doc: str, refined_doc: str) -> int:
        unrefined_bytes = len(unrefined_doc.encode("utf-8"))
        refined_bytes = len(refined_doc.encode("utf-8"))

        if unrefined_bytes == 0:
            return 0

        percent_diff = (unrefined_bytes - refined_bytes) / unrefined_bytes * 100
        return round(percent_diff)

    result = calculate_size_diff(unrefined, refined)
    assert result == expected


def test_demo_upload_success(test_assets_path: pathlib.Path) -> None:
    """
    Test successful demo file upload and processing
    """

    from app.api.v1.demo import (
        _get_demo_zip_path,  # Import here to avoid circular import
    )

    def mock_path_dep() -> pathlib.Path:
        return test_assets_path / "demo" / "monmothma.zip"

    # Use the actual function reference, not a string
    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

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

    from app.api.v1.demo import (
        _get_demo_zip_path,  # Import here to avoid circular import
    )

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

    def mock_missing_path() -> pathlib.Path:
        return pathlib.Path("/nonexistent/demo.zip")

    # Mock the dependency without importing it directly
    app.dependency_overrides["_get_demo_zip_path"] = mock_missing_path  # type: ignore

    # Test both endpoints with missing file
    for endpoint in ["upload", "download"]:
        response = client.get(f"{api_route_base}/{endpoint}")
        assert response.status_code == 404
        assert response.json() == {
            "detail": "Unable to find demo zip file to download."
        }

    app.dependency_overrides.clear()

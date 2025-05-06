import pathlib

import pytest
from fastapi.testclient import TestClient

from app.api.v1.demo import _get_demo_zip_path
from app.main import app

client = TestClient(app)

api_route_base = "/api/demo"


def test_demo_upload_success():
    def mock_path_dep():
        return (
            pathlib.Path(__file__).parent.parent.parent
            / "tests"
            / "assets"
            / "demo"
            / "monmothma.zip"
        )

    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

    response = client.get(f"{api_route_base}/upload")

    # just checking for success since all other code is checked in other tests
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_demo_upload_file_missing():
    def mock_path_dep():
        return pathlib.Path("/nonexistent/path/monmothma.zip")

    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

    response = client.get(f"{api_route_base}/upload")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unable to find demo zip file to download."}

    app.dependency_overrides.clear()


def test_demo_upload_processing_error(monkeypatch, tmp_path):
    with pytest.raises(ValueError):
        zip_file_path = tmp_path / "demo.zip"
        zip_file_path.write_bytes(b"invalid zip content")

        def mock_path_dep():
            return zip_file_path

        app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

        def raise_error(file):
            raise ValueError("Broken zip")

        # patching this so that it will fail
        monkeypatch.setattr("app.api.v1.demo.read_zip", raise_error)

        response = client.get(f"{api_route_base}/upload")

        # FastAPI should throw a generic 500 response
        assert response.status_code == 500
        assert "Internal Server Error" in response.text or "detail" in response.json()

        app.dependency_overrides.clear()


def test_demo_download_success(tmp_path):
    fake_zip = tmp_path / "mocked.zip"
    fake_zip.write_bytes(b"Fake zip content")

    def mock_path_dep():
        return fake_zip

    app.dependency_overrides[_get_demo_zip_path] = mock_path_dep

    response = client.get(f"{api_route_base}/download")
    assert response.status_code == 200

    content_disposition = response.headers.get("content-disposition", "")
    expected_filename = "mocked.zip"
    assert f'filename="{expected_filename}"' in content_disposition

    assert response.content == b"Fake zip content"

    app.dependency_overrides.clear()


def test_demo_download_file_not_found():
    def mock_missing_file_path():
        return pathlib.Path("/some/fake/path/nonexistent.zip")

    app.dependency_overrides[_get_demo_zip_path] = mock_missing_file_path

    response = client.get(f"{api_route_base}/download")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unable to find demo zip file to download."}

    app.dependency_overrides.clear()

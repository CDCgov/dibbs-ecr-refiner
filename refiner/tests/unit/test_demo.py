from pathlib import Path

import pytest

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

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from app.api.auth.middleware import get_logged_in_user
from app.db.users.model import DbUser
from app.main import app

api_route_base = "/api/v1/downloads"


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return DbUser(
        id=UUID("673da667-6f92-4a50-a40d-f44c5bc6a2d8"),
        username="test-user",
        email="test@test.com",
        jurisdiction_id="SDDH",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def different_user():
    """Create a different mock user for testing unauthorized access."""
    return DbUser(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        username="other-user",
        email="other@test.com",
        jurisdiction_id="SDDH",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def create_mock_s3_response(content: bytes = b"mock zip content"):
    """Create a mock S3 get_object response."""
    mock_body = MagicMock()
    mock_body.iter_chunks.return_value = iter([content])
    return {"Body": mock_body}


class TestDownloadRefinedEcr:
    """Tests for the download_refined_ecr endpoint."""

    def test_successful_download(self, mock_user):
        """Test successful file download when user owns the file."""
        # Set up auth override
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        # Create a valid S3 key for this user
        s3_key = f"refiner-test-suite/2026-01-29/{mock_user.id}/test-file.zip"

        # Mock the S3 client
        with patch("app.api.v1.downloads.s3_client") as mock_s3:
            mock_s3.get_object.return_value = create_mock_s3_response()

            client = TestClient(app)
            response = client.get(f"{api_route_base}/{s3_key}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
            assert (
                response.headers["content-disposition"]
                == 'attachment; filename="test-file.zip"'
            )
            assert response.content == b"mock zip content"

            # Verify S3 was called with correct parameters
            mock_s3.get_object.assert_called_once()

        app.dependency_overrides.clear()

    def test_forbidden_when_user_doesnt_own_file(self, mock_user, different_user):
        """Test that users cannot download files owned by other users."""
        # Authenticate as mock_user
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        # Try to download a file owned by different_user
        s3_key = f"refiner-test-suite/2026-01-29/{different_user.id}/other-file.zip"

        client = TestClient(app)
        response = client.get(f"{api_route_base}/{s3_key}")

        assert response.status_code == 403
        assert response.json() == {
            "detail": "You do not have permission to download this file."
        }

        app.dependency_overrides.clear()

    def test_forbidden_when_key_has_invalid_user_id(self, mock_user):
        """Test that requests with invalid user IDs in the key are rejected."""
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        # S3 key with an invalid UUID
        s3_key = "refiner-test-suite/2026-01-29/not-a-valid-uuid/file.zip"

        client = TestClient(app)
        response = client.get(f"{api_route_base}/{s3_key}")

        assert response.status_code == 403
        assert response.json() == {
            "detail": "You do not have permission to download this file."
        }

        app.dependency_overrides.clear()

    def test_forbidden_when_key_has_wrong_format(self, mock_user):
        """Test that requests with malformed keys are rejected."""
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        # S3 key with wrong prefix
        s3_key = f"wrong-prefix/2026-01-29/{mock_user.id}/file.zip"

        client = TestClient(app)
        response = client.get(f"{api_route_base}/{s3_key}")

        assert response.status_code == 403
        assert response.json() == {
            "detail": "You do not have permission to download this file."
        }

        app.dependency_overrides.clear()

    def test_not_found_when_s3_key_doesnt_exist(self, mock_user):
        """Test that a 404 is returned when the S3 key doesn't exist."""
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        s3_key = f"refiner-test-suite/2026-01-29/{mock_user.id}/nonexistent.zip"

        with patch("app.api.v1.downloads.s3_client") as mock_s3:
            # Simulate S3 NoSuchKey error
            mock_s3.get_object.side_effect = ClientError(
                {
                    "Error": {
                        "Code": "NoSuchKey",
                        "Message": "The specified key does not exist.",
                    }
                },
                "GetObject",
            )

            client = TestClient(app)
            response = client.get(f"{api_route_base}/{s3_key}")

            assert response.status_code == 404
            assert response.json() == {"detail": "File not found."}

        app.dependency_overrides.clear()

    def test_server_error_on_s3_failure(self, mock_user):
        """Test that a 500 is returned when S3 has an unexpected error."""
        app.dependency_overrides[get_logged_in_user] = lambda: mock_user

        s3_key = f"refiner-test-suite/2026-01-29/{mock_user.id}/file.zip"

        with patch("app.api.v1.downloads.s3_client") as mock_s3:
            # Simulate unexpected S3 error
            mock_s3.get_object.side_effect = ClientError(
                {"Error": {"Code": "InternalError", "Message": "Internal error"}},
                "GetObject",
            )

            client = TestClient(app)
            response = client.get(f"{api_route_base}/{s3_key}")

            assert response.status_code == 500
            assert response.json() == {
                "detail": "An error occurred while retrieving the file."
            }

        app.dependency_overrides.clear()

    def test_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        # Don't override the auth dependency - it will require a real session
        app.dependency_overrides.clear()

        client = TestClient(app)
        s3_key = "refiner-test-suite/2026-01-29/some-user-id/file.zip"

        response = client.get(f"{api_route_base}/{s3_key}")

        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestParseUserIdFromKey:
    """Tests for the _parse_user_id_from_key helper function."""

    def test_valid_key_returns_uuid(self):
        """Test parsing a valid S3 key."""
        from app.api.v1.downloads import _parse_user_id_from_key

        user_id = UUID("673da667-6f92-4a50-a40d-f44c5bc6a2d8")
        key = f"refiner-test-suite/2026-01-29/{user_id}/file.zip"

        result = _parse_user_id_from_key(key)

        assert result == user_id

    def test_invalid_prefix_returns_none(self):
        """Test that keys with wrong prefix return None."""
        from app.api.v1.downloads import _parse_user_id_from_key

        key = "wrong-prefix/2026-01-29/673da667-6f92-4a50-a40d-f44c5bc6a2d8/file.zip"

        result = _parse_user_id_from_key(key)

        assert result is None

    def test_invalid_uuid_returns_none(self):
        """Test that keys with invalid UUIDs return None."""
        from app.api.v1.downloads import _parse_user_id_from_key

        key = "refiner-test-suite/2026-01-29/not-a-uuid/file.zip"

        result = _parse_user_id_from_key(key)

        assert result is None

    def test_too_few_parts_returns_none(self):
        """Test that keys with too few path segments return None."""
        from app.api.v1.downloads import _parse_user_id_from_key

        key = "refiner-test-suite/2026-01-29"

        result = _parse_user_id_from_key(key)

        assert result is None


class TestGetFilenameFromKey:
    """Tests for the _get_filename_from_key helper function."""

    def test_extracts_filename(self):
        """Test extracting filename from a valid key."""
        from app.api.v1.downloads import _get_filename_from_key

        key = "refiner-test-suite/2026-01-29/user-id/my-refined-ecr.zip"

        result = _get_filename_from_key(key)

        assert result == "my-refined-ecr.zip"

    def test_handles_key_without_slashes(self):
        """Test handling a key with no slashes."""
        from app.api.v1.downloads import _get_filename_from_key

        key = "just-a-filename.zip"

        result = _get_filename_from_key(key)

        assert result == "just-a-filename.zip"

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuth:
    """
    Tests for API authentication.
    """

    async def test_no_user(setup, base_url):
        """
        Should return 401 Unauthorized when trying to hit a protected route
        while not logged in.
        """
        async with AsyncClient(base_url=base_url) as client:
            response = await client.post("/api/v1/demo/upload")
            assert response.status_code == 401

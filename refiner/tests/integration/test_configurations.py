import pytest

base_route = "/api/v1/configurations/"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_configurations_returns_expected_data(authed_client):
    response = await authed_client.get(base_route)
    assert response.status_code == 200

    data = response.json()

    # Data is a list with expected elements
    assert isinstance(data, list)
    assert len(data) == 5

    # Check an item's shape
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "is_active" in first

    # Check values
    assert first["name"] == "Chlamydia trachomatis infection"
    assert first["is_active"] is True

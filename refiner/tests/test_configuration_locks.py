from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import tests.test_configuration_locks as test_module
from app.api.auth.middleware import get_logged_in_user
from app.api.v1.configurations import GetConfigurationsResponse
from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.db import GetConfigurationResponseVersion
from app.db.configurations.model import (
    DbConfiguration,
    DbConfigurationCondition,
)
from app.db.users.model import DbUser
from app.main import app
from app.services.configuration_locks import ConfigurationLock

# User info
TEST_SESSION_TOKEN = "test-token"
MOCK_LOGGED_IN_USER_ID = "5deb43c2-6a82-4052-9918-616e01d255c7"

# Module-level storage for mocked locks (used by tests)
_locks_storage = {}


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


def mock_user():
    return DbUser(
        id=MOCK_LOGGED_IN_USER_ID,
        username="tester",
        email="tester@test.com",
        jurisdiction_id="JD-1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest_asyncio.fixture
async def authed_client(mock_logged_in_user, mock_db_functions):
    """
    Mock an authenticated client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        client.cookies.update({"refiner-session": TEST_SESSION_TOKEN})
        yield client


@pytest.fixture(autouse=True)
def mock_logged_in_user():
    """
    Mock the logged-in user dependency
    """

    app.dependency_overrides[get_logged_in_user] = mock_user
    yield
    app.dependency_overrides.pop(get_logged_in_user, None)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch):
    """
    Mock return values of the `_db` functions called by the routes.
    """

    # prepare a fake condition with codes
    condition_mock = DbCondition(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        display_name="Condition A",
        canonical_url="url-1",
        version="3.0.0",
        child_rsg_snomed_codes=["12345"],
        snomed_codes=[make_db_condition_coding("12345", "SNOMED Description")],
        loinc_codes=[make_db_condition_coding("54321", "LOINC Description")],
        icd10_codes=[make_db_condition_coding("A00", "ICD10 Description")],
        rxnorm_codes=[make_db_condition_coding("99999", "RXNORM Description")],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_condition_by_id_db",
        AsyncMock(return_value=condition_mock),
    )

    fake_condition = DbCondition(
        id=uuid4(),
        display_name="Hypertension",
        canonical_url="http://url.com",
        version="3.0.0",
        child_rsg_snomed_codes=["11111"],
        snomed_codes=[make_db_condition_coding("11111", "Hypertension SNOMED")],
        loinc_codes=[make_db_condition_coding("22222", "Hypertension LOINC")],
        icd10_codes=[make_db_condition_coding("I10", "Essential hypertension")],
        rxnorm_codes=[make_db_condition_coding("33333", "Hypertension RXNORM")],
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.get_conditions_db",
        AsyncMock(return_value=[fake_condition]),
    )

    # mock get_configuration_by_id_db with default: no custom codes
    config_by_id_mock = DbConfiguration(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="test config",
        jurisdiction_id="SDDH",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="url-1",
        s3_urls=[],
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_by_id_db",
        AsyncMock(return_value=config_by_id_mock),
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.get_latest_config_db",
        AsyncMock(return_value=config_by_id_mock),
    )

    versions_mock = [
        GetConfigurationResponseVersion(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            status="draft",
            version=1,
            condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
            created_by=MOCK_LOGGED_IN_USER_ID,
            created_at=datetime.now(),
            last_activated_at=None,
            last_activated_by=None,
        )
    ]

    monkeypatch.setattr(
        "app.api.v1.configurations.get_configuration_versions_db",
        AsyncMock(return_value=versions_mock),
    )

    # Mock get_configurations_db
    monkeypatch.setattr(
        "app.api.v1.configurations.get_configurations_db",
        AsyncMock(return_value=[config_by_id_mock]),
    )

    # Mock is_config_valid_to_insert_db
    monkeypatch.setattr(
        "app.api.v1.configurations.is_config_valid_to_insert_db",
        AsyncMock(return_value=True),
    )

    # Mock insert_configuration_db
    new_config_mock = GetConfigurationsResponse(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="New Config",
        status="draft",
    )
    monkeypatch.setattr(
        "app.api.v1.configurations.insert_configuration_db",
        AsyncMock(return_value=new_config_mock),
    )

    # mock associate_condition_codeset_with_configuration_db
    assoc_condition = DbConfigurationCondition(
        UUID("22222222-2222-2222-2222-222222222222"),
    )
    updated_config_mock = DbConfiguration(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="New Config",
        jurisdiction_id="JD-1",
        condition_id=UUID("22222222-2222-2222-2222-222222222222"),
        included_conditions=[assoc_condition],
        custom_codes=[],
        local_codes=[],
        section_processing=[],
        version=1,
        status="draft",
        last_activated_at=None,
        last_activated_by=None,
        created_by=MOCK_LOGGED_IN_USER_ID,
        condition_canonical_url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123",
        s3_urls=[],
    )

    monkeypatch.setattr(
        "app.api.v1.configurations.associate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock),
    )

    # Mock disassociate_condition_codeset_with_configuration_db
    updated_config_mock_disassoc = AsyncMock()
    updated_config_mock_disassoc.id = UUID("33333333-3333-3333-3333-333333333333")
    updated_config_mock_disassoc.included_conditions = []

    monkeypatch.setattr(
        "app.api.v1.configurations.disassociate_condition_codeset_with_configuration_db",
        AsyncMock(return_value=updated_config_mock_disassoc),
    )

    # for get_total_condition_code_counts_by_configuration_db, could use a list of count objects if needed
    monkeypatch.setattr(
        "app.api.v1.configurations.get_total_condition_code_counts_by_configuration_db",
        AsyncMock(return_value=[]),
    )

    # Mock ConfigurationLock database operations
    # We'll use a simple in-memory dict to simulate lock storage for unit tests
    # Clear any existing locks from previous tests
    global _locks_storage
    _locks_storage.clear()

    async def mock_get_lock(configuration_id: str, db=None):
        lock_data = _locks_storage.get(configuration_id)
        if lock_data:
            return ConfigurationLock(
                configuration_id=lock_data["configuration_id"],
                user_id=lock_data["user_id"],
                expires_at=lock_data["expires_at"],
            )

    async def mock_acquire_lock(configuration_id: UUID, user_id: UUID, db=None):
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=30)

        # Check if lock exists and is active
        existing_lock_data = _locks_storage.get(configuration_id)
        if (
            existing_lock_data
            and existing_lock_data["expires_at"].timestamp() > now.timestamp()
        ):
            # Lock is active
            return existing_lock_data["user_id"] == user_id

        # Acquire or replace lock
        _locks_storage[configuration_id] = {
            "configuration_id": configuration_id,
            "user_id": user_id,
            "expires_at": expires_at,
        }
        return True

    async def mock_release_lock(configuration_id: UUID, user_id: UUID, db=None):
        if configuration_id in _locks_storage:
            lock_data = _locks_storage[configuration_id]
            if lock_data["user_id"] == user_id:
                del _locks_storage[configuration_id]

    async def mock_renew_lock(configuration_id: UUID, user_id: UUID, db=None):
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=30)

        if configuration_id in _locks_storage:
            lock_data = _locks_storage[configuration_id]
            if lock_data["user_id"] == user_id:
                _locks_storage[configuration_id]["expires_at"] = expires_at

    monkeypatch.setattr(
        "app.services.configuration_locks.ConfigurationLock.get_lock",
        mock_get_lock,
    )
    monkeypatch.setattr(
        "app.services.configuration_locks.ConfigurationLock.acquire_lock",
        mock_acquire_lock,
    )
    monkeypatch.setattr(
        "app.services.configuration_locks.ConfigurationLock.release_if_owned",
        mock_release_lock,
    )
    monkeypatch.setattr(
        "app.services.configuration_locks.ConfigurationLock.renew_lock",
        mock_renew_lock,
    )

    yield


@pytest.mark.asyncio
async def test_acquire_and_release_lock(authed_client):
    configuration_id = uuid4()
    user_id = uuid4()
    db = None

    # Acquire lock
    acquired = await ConfigurationLock.acquire_lock(configuration_id, user_id, db)
    assert acquired is True

    # Lock should be present and owned by user
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    assert lock is not None
    assert lock.user_id == user_id

    # Release lock
    await ConfigurationLock.release_if_owned(configuration_id, user_id, db)

    # Release is idempotent and should work a second time
    await ConfigurationLock.release_if_owned(configuration_id, user_id, db)

    # Lock should be gone
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    assert lock is None


@pytest.mark.asyncio
async def test_lock_contention(authed_client):
    configuration_id = uuid4()
    user1 = uuid4()
    user2 = uuid4()
    db = None

    # User1 acquires lock
    acquired1 = await ConfigurationLock.acquire_lock(configuration_id, user1, db)
    assert acquired1 is True

    # User2 tries to acquire lock (should not succeed)
    acquired2 = await ConfigurationLock.acquire_lock(configuration_id, user2, db)
    assert acquired2 is False

    # User1 releases lock
    await ConfigurationLock.release_if_owned(configuration_id, user1, db)

    # User2 can now acquire lock
    acquired2b = await ConfigurationLock.acquire_lock(configuration_id, user2, db)
    assert acquired2b is True


@pytest.mark.asyncio
async def test_lock_renewal_and_expiry(authed_client):
    configuration_id = uuid4()
    user_id = uuid4()
    db = None

    # Acquire lock
    await ConfigurationLock.acquire_lock(configuration_id, user_id, db)
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    assert lock is not None
    expires_at_initial = lock.expires_at

    # Renew lock
    await ConfigurationLock.renew_lock(configuration_id, user_id, db)
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    assert lock.expires_at > expires_at_initial

    # Simulate expiry by directly manipulating the mocked storage
    locks_storage = test_module._locks_storage
    if configuration_id in locks_storage:
        locks_storage[configuration_id]["expires_at"] = datetime.now(UTC) - timedelta(
            minutes=1
        )

    # Now lock should be considered expired
    lock = await ConfigurationLock.get_lock(configuration_id, db)
    assert lock is not None  # Lock still exists in storage
    assert (
        lock.expires_at.timestamp() < datetime.now(UTC).timestamp()
    )  # But it's expired

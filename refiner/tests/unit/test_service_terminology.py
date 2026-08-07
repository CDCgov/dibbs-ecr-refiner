from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.conditions.model import DbCondition, DbConditionCoding
from app.db.configurations.model import (
    DbConfiguration,
)
from app.db.custom_codes.model import DbCustomCode
from tests.unit.helpers.configuration import create_processed_config


def make_db_condition_coding(code, display):
    return DbConditionCoding(code=code, display=display)


def make_condition(**kwargs) -> DbCondition:
    defaults = {
        "id": uuid4(),
        "display_name": "Condition",
        "canonical_url": "http://cond.com",
        "version": "1.0.0",
        "child_rsg_snomed_codes": [],
        "snomed_codes": [],
        "loinc_codes": [],
        "icd10_codes": [],
        "rxnorm_codes": [],
        "cvx_codes": [],
    }
    defaults.update(kwargs)
    return DbCondition(**defaults)


def make_dbconfiguration(**kwargs) -> DbConfiguration:
    defaults = {
        "id": uuid4(),
        "name": "Test Config",
        "jurisdiction_id": "JD-1",
        "condition_id": uuid4(),
        "included_conditions": [],
        "custom_codes": [],
        "section_processing": [],
        "version": 1,
        "status": "draft",
        "last_activated_at": None,
        "last_activated_by": None,
        "created_by": uuid4(),
        "s3_url": "",
    }
    defaults.update(kwargs)
    return DbConfiguration(**defaults)


@pytest.fixture(autouse=True)
def mock_db_functions(monkeypatch, mock_all_systems):
    """
    Mock return values of the `_db` functions called by the routes.
    """
    monkeypatch.setattr(
        "app.services.code_systems.get_all_code_systems_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_all_code_systems_db",
        AsyncMock(return_value={m.id: m for m in mock_all_systems}),
    )

    monkeypatch.setattr(
        "app.services.configurations.get_code_system_by_key_db",
        AsyncMock(
            side_effect=lambda key, db: next(
                m for m in mock_all_systems if m.key == key
            ),
        ),
    )


@pytest.mark.asyncio
class TestTerminologyService:
    async def test_processed_configuration_from_payload_and_xpath(
        self, get_mock_system
    ):
        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("A", "SNOMED")]
        )

        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            id=mock_config_id,
            custom_codes=[
                DbCustomCode(
                    id="test-code",
                    code="B",
                    display="Custom LOINC",
                    system_id=loinc.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                    configuration_id=mock_config_id,
                )
            ],
        )
        processed = await create_processed_config(config=config, conditions=[cond1])
        assert processed.codes == {"A", "B"}

    async def test_processed_configuration_duplicate_codes(self, get_mock_system):
        cond1: DbCondition = make_condition(
            snomed_codes=[make_db_condition_coding("DUP", "SNOMED")]
        )
        cond2: DbCondition = make_condition(
            loinc_codes=[make_db_condition_coding("DUP", "LOINC")]
        )
        loinc = get_mock_system("loinc")

        mock_config_id = uuid4()
        config: DbConfiguration = make_dbconfiguration(
            custom_codes=[
                DbCustomCode(
                    id="test-code",
                    code="DUP",
                    display="Custom",
                    system_id=loinc.id,
                    updated_at=datetime.now(),
                    created_at=datetime.now(),
                    configuration_id=mock_config_id,
                )
            ]
        )

        processed = await create_processed_config(
            config=config, conditions=[cond1, cond2]
        )
        assert processed.codes == {"DUP"}


@pytest.mark.asyncio
class TestCodeExclusions:
    """
    Exclusion ("de-selection") removes a condition-contributed code from the
    want-set during projection, before `active.json` is built. Because
    refinement is retention-by-inclusion, a code absent from the want-set
    retains nothing -- so these tests assert on the projected want-set rather
    than on refined XML.
    """

    async def test_excluded_code_is_absent_from_want_set(self):
        condition = make_condition(
            snomed_codes=[
                make_db_condition_coding("KEEP", "Kept"),
                make_db_condition_coding("DROP", "Excluded"),
            ]
        )
        config = make_dbconfiguration()

        processed = await create_processed_config(
            config=config,
            conditions=[condition],
            excluded_codes={condition.id: {("snomed", "DROP")}},
        )

        assert processed.codes == {"KEEP"}

    async def test_exclusion_is_scoped_to_its_condition(self):
        """
        Exclusions are keyed by (configuration, condition), but `active.json`
        flattens every included condition into one want-set. So excluding a
        code from one condition does NOT remove it when a second included
        condition still contributes it -- the want-set is a union.

        This is load-bearing: roughly half of all seeded codes appear in more
        than one condition, so this is the common case, not an edge case.
        """

        cond1 = make_condition(snomed_codes=[make_db_condition_coding("SHARED", "One")])
        cond2 = make_condition(snomed_codes=[make_db_condition_coding("SHARED", "Two")])
        config = make_dbconfiguration()

        processed = await create_processed_config(
            config=config,
            conditions=[cond1, cond2],
            excluded_codes={cond1.id: {("snomed", "SHARED")}},
        )

        assert processed.codes == {"SHARED"}

    async def test_exclusion_is_scoped_to_its_code_system(self):
        condition = make_condition(
            snomed_codes=[make_db_condition_coding("1234", "SNOMED 1234")],
            loinc_codes=[make_db_condition_coding("1234", "LOINC 1234")],
        )
        config = make_dbconfiguration()

        processed = await create_processed_config(
            config=config,
            conditions=[condition],
            excluded_codes={condition.id: {("loinc", "1234")}},
        )

        maps = processed.code_system_sets.system_to_code_maps
        assert "1234" in maps["snomed"]
        assert "1234" not in maps["loinc"]

    async def test_exclusion_never_strips_a_matching_custom_code(self, get_mock_system):
        """
        The anti-join runs inside the per-condition loop, which custom codes
        never pass through. So a hand-added custom code survives even when it
        collides with an excluded condition code on (system, code).

        The code therefore stays in the want-set. That is correct -- the user
        added it deliberately -- but it will read as a failed exclusion, so the
        behavior is pinned here rather than left to chance.
        """

        loinc = get_mock_system("loinc")
        condition = make_condition(
            loinc_codes=[make_db_condition_coding("COLLIDE", "From condition")]
        )
        config_id = uuid4()
        config = make_dbconfiguration(
            id=config_id,
            custom_codes=[
                DbCustomCode(
                    id="custom-1",
                    code="COLLIDE",
                    display="Hand added",
                    system_id=loinc.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    configuration_id=config_id,
                )
            ],
        )

        processed = await create_processed_config(
            config=config,
            conditions=[condition],
            excluded_codes={condition.id: {("loinc", "COLLIDE")}},
        )

        assert processed.codes == {"COLLIDE"}
        assert (
            processed.code_system_sets.system_to_code_maps["loinc"]["COLLIDE"].display
            == "Hand added"
        )

    async def test_no_exclusions_leaves_want_set_untouched(self):
        condition = make_condition(
            snomed_codes=[make_db_condition_coding("A", "A")],
            loinc_codes=[make_db_condition_coding("B", "B")],
        )
        config = make_dbconfiguration()

        with_none = await create_processed_config(
            config=config, conditions=[condition], excluded_codes={}
        )
        baseline = await create_processed_config(config=config, conditions=[condition])

        assert with_none.codes == baseline.codes == {"A", "B"}

    async def test_exclusion_for_an_unrelated_condition_is_ignored(self):
        condition = make_condition(
            snomed_codes=[make_db_condition_coding("A", "A")],
        )
        config = make_dbconfiguration()

        processed = await create_processed_config(
            config=config,
            conditions=[condition],
            excluded_codes={uuid4(): {("snomed", "A")}},
        )

        assert processed.codes == {"A"}

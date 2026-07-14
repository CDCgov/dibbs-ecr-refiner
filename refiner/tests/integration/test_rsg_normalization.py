from uuid import uuid4

import pytest

from app.db.conditions.db import (
    get_condition_by_id_db,
    get_conditions_by_child_rsg_snomed_codes_db,
)


@pytest.mark.asyncio
async def test_rsg_code_redirection(db_pool):
    """
    Verifies that data is retrieved from the normalized join tables
    rather than the legacy `child_rsg_snomed_codes` column.
    """
    condition_id = uuid4()
    tes_id = uuid4()
    code_id = uuid4()

    legacy_code = "LEGACY_123"
    new_code = "NORMALIZED_456"

    # 1. Setup: Create minimal dependencies
    async with db_pool.get_connection() as conn:
        async with conn.cursor() as cur:
            # Get an existing TES record to avoid UniqueViolation on version
            await cur.execute("SELECT id FROM tes LIMIT 1")
            tes_row = await cur.fetchone()
            if tes_row:
                tes_id = tes_row[0]
            else:
                tes_id = uuid4()
                await cur.execute(
                    "INSERT INTO tes (id, version) VALUES (%s, %s)",
                    (tes_id, f"test-version-{uuid4()}"),
                )

            # Insert Condition with a value in the LEGACY column
            await cur.execute(
                """
                INSERT INTO conditions (
                    id, tes_id, display_name, canonical_url,
                    child_rsg_snomed_codes, snomed_codes, loinc_codes,
                    icd10_codes, rxnorm_codes, cvx_codes
                ) VALUES (%s, %s, %s, %s, %s, '[]', '[]', '[]', '[]', '[]')
                """,
                (
                    condition_id,
                    tes_id,
                    "Test Condition",
                    "http://test.com",
                    [legacy_code],
                ),
            )

            # Insert a DIFFERENT code in the normalized tables
            await cur.execute("SELECT id FROM systems LIMIT 1")
            system_row = await cur.fetchone()
            system_id = system_row[0] if system_row else uuid4()
            if not system_row:
                await cur.execute(
                    "INSERT INTO systems (id, key, display_name) VALUES (%s, %s, %s)",
                    (system_id, "snomed", "SNOMED"),
                )

            await cur.execute(
                "INSERT INTO codes (id, code, display, version, system_id) VALUES (%s, %s, %s, %s, %s)",
                (code_id, new_code, "Normalized Display", "1.0.0", system_id),
            )
            await cur.execute(
                "INSERT INTO conditions_rsg_codes (condition_id, code_id) VALUES (%s, %s)",
                (condition_id, code_id),
            )
            await conn.commit()

    # 2. Verify get_condition_by_id_db ignores legacy column
    condition = await get_condition_by_id_db(condition_id, db_pool)
    assert condition is not None
    assert new_code in condition.child_rsg_snomed_codes
    assert legacy_code not in condition.child_rsg_snomed_codes

    # 3. Verify get_conditions_by_child_rsg_snomed_codes_db uses join table
    # Search for the new code -> should find the condition
    results_new = await get_conditions_by_child_rsg_snomed_codes_db(db_pool, [new_code])
    assert len(results_new) == 1
    assert results_new[0].id == condition_id

    # Search for the legacy code -> should NOT find the condition
    results_legacy = await get_conditions_by_child_rsg_snomed_codes_db(
        db_pool, [legacy_code]
    )
    assert len(results_legacy) == 0

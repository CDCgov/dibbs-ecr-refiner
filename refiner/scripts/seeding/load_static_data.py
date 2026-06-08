import os
import time
from collections import defaultdict
from datetime import datetime
from typing import TypedDict
from uuid import UUID, uuid4

from config import ENV_PATH, logger
from dotenv import load_dotenv
from lib import (
    CODE_SYSTEM_DATA,
    SNOMED_OID,
    CodeRow,
    ConditionData,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
    get_child_rsg_valuesets,
    get_db_connection,
    is_condition_grouper,
    load_valuesets_from_all_files,
    parse_snomed_from_url,
)
from psycopg import Cursor
from psycopg.rows import TupleRow


class Code(TypedDict):
    """
    A code object in a condition's code set.
    """

    code: str
    display: str


class ConditionRow(TypedDict):
    """
    A condition row to upsert into the DB.
    """

    id: UUID
    canonical_url: str
    version: str
    display_name: str
    child_rsg_snomed_codes: list[str] | None
    loinc_codes: list[Code] | None
    snomed_codes: list[Code] | None
    icd10_codes: list[Code] | None
    rxnorm_codes: list[Code] | None
    cvx_codes: list[Code] | None
    coverage_level: str | None
    coverage_level_reason: str | None
    coverage_level_date: datetime | None


class ContextGrouperRow(TypedDict):
    """
    A context grouper row to upsert into the DB.
    """

    name: str
    category: str
    canonical_url: str
    code_count: int


class ProcessedCondition(TypedDict):
    """
    A fully processed condition with its associated context grouper rows.
    """

    condition: ConditionRow
    context_groupers: list[ContextGrouperRow]


type SystemDbId = str
type SystemOid = str


class ConditionToCodeRelationshipTrace(TypedDict):
    """
    A trace object to keep track of condition <> code relationships to seed the relevant join tables.
    """

    condition_id: UUID
    condition_display_name: str
    child_rsg_snomed_code_ids: list[UUID]
    version: str


type ConditionUniqueIndex = tuple[VsCanonicalUrl, VsVersion]

type ConditionToCodeRelationshipIndex = dict[
    ConditionUniqueIndex, ConditionToCodeRelationshipTrace
]


def _parse_display_text_from_use_context(use_context: list[dict[str, dict]]) -> str:
    for context in use_context:
        value_codeable_concept = context.get("valueCodeableConcept", "")
        if not isinstance(value_codeable_concept, str):
            vs_description = value_codeable_concept.get("text", None)
            # one of the use contexts in the RSG files is a description of
            # "this code is an RSG code". Skip that one.
            if (
                isinstance(vs_description, str)
                and vs_description != "Reporting Specification Grouper"
            ):
                return vs_description

    raise ValueError("No description found in parsing child RSG display name")


def _build_rsg_codes(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
    condition_groupers: list[VsDict],
    system_data: dict[SystemOid, SystemDbId],
    condition_to_code_relationships: ConditionToCodeRelationshipIndex,
) -> tuple[list[CodeRow], ConditionToCodeRelationshipIndex]:
    snomed_db_id = system_data[SNOMED_OID]
    rsg_codes: list[CodeRow] = []

    for parent in condition_groupers:
        child_rsg_code_ids: list[UUID] = []
        cond_canonical_url = parent.get("url", "")
        cond_version = parent.get("version", "")

        for child_vs in get_child_rsg_valuesets(
            parent=parent, all_vs_map=valuesets_map
        ):
            if snomed_code := parse_snomed_from_url(child_vs.get("url", "")):
                name = _parse_display_text_from_use_context(
                    child_vs.get("useContext", "")
                )
                child_code_db_id = uuid4()
                child_rsg_code_ids.append(child_code_db_id)
                rsg_codes.append(
                    CodeRow(
                        id=child_code_db_id,
                        value=snomed_code,
                        version=cond_version,
                        name=name,
                        system_id=snomed_db_id,
                    )
                )

        cond_index = (cond_canonical_url, cond_version)
        if len(child_rsg_code_ids) > 0 and cond_index in list(
            condition_to_code_relationships.keys()
        ):
            relationship = condition_to_code_relationships[cond_index]
            relationship.get("child_rsg_snomed_code_ids").extend(child_rsg_code_ids)

    return (rsg_codes, condition_to_code_relationships)


def _build_processed_conditions(
    condition_groupers: list[VsDict],
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
) -> list[ProcessedCondition]:
    results: list[ProcessedCondition] = []

    for parent in condition_groupers:
        data = ConditionData(parent, valuesets_map)
        results.append(
            {
                "condition": data.payload,
                "context_groupers": data.context_grouper_payloads,
            }
        )

    logger.info(f"🛠️  Total condition rows processed: {len(results)}")
    return results


def _upsert_conditions_and_groupers(
    cursor: Cursor,
    processed: list[ProcessedCondition],
) -> ConditionToCodeRelationshipIndex:
    """
    Upserts condition rows and their associated context grouper rows.

    Each condition is upserted using a CTE that returns the row's id
    regardless of whether the row was inserted, updated, or unchanged.
    Context grouper rows are then upserted as children of that condition.

    Both upserts use IS DISTINCT FROM to avoid touching rows where
    nothing has changed, preventing spurious updated_at timestamps.
    """

    logger.info("⏳ Upserting condition records...")

    condition_upsert_query = """
        WITH upsert_condition AS (
            INSERT INTO conditions (
                id,
                canonical_url,
                version,
                display_name,
                child_rsg_snomed_codes,
                loinc_codes,
                snomed_codes,
                icd10_codes,
                rxnorm_codes,
                cvx_codes,
                coverage_level,
                coverage_level_reason,
                coverage_level_date
            )
            VALUES (
                %(id)s,
                %(canonical_url)s,
                %(version)s,
                %(display_name)s,
                %(child_rsg_snomed_codes)s,
                %(loinc_codes)s,
                %(snomed_codes)s,
                %(icd10_codes)s,
                %(rxnorm_codes)s,
                %(cvx_codes)s,
                %(coverage_level)s,
                %(coverage_level_reason)s,
                %(coverage_level_date)s
            )
            ON CONFLICT (canonical_url, version)
            DO UPDATE SET
                id = EXCLUDED.id,
                display_name = EXCLUDED.display_name,
                child_rsg_snomed_codes = EXCLUDED.child_rsg_snomed_codes,
                loinc_codes = EXCLUDED.loinc_codes,
                snomed_codes = EXCLUDED.snomed_codes,
                icd10_codes = EXCLUDED.icd10_codes,
                rxnorm_codes = EXCLUDED.rxnorm_codes,
                cvx_codes = EXCLUDED.cvx_codes,
                coverage_level = EXCLUDED.coverage_level,
                coverage_level_reason = EXCLUDED.coverage_level_reason,
                coverage_level_date = EXCLUDED.coverage_level_date
            WHERE
                conditions.id IS DISTINCT FROM EXCLUDED.id
                OR conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
                OR conditions.child_rsg_snomed_codes IS DISTINCT FROM EXCLUDED.child_rsg_snomed_codes
                OR conditions.loinc_codes IS DISTINCT FROM EXCLUDED.loinc_codes
                OR conditions.snomed_codes IS DISTINCT FROM EXCLUDED.snomed_codes
                OR conditions.icd10_codes IS DISTINCT FROM EXCLUDED.icd10_codes
                OR conditions.rxnorm_codes IS DISTINCT FROM EXCLUDED.rxnorm_codes
                OR conditions.cvx_codes IS DISTINCT FROM EXCLUDED.cvx_codes
                OR conditions.coverage_level IS DISTINCT FROM EXCLUDED.coverage_level
                OR conditions.coverage_level_reason IS DISTINCT FROM EXCLUDED.coverage_level_reason
                OR conditions.coverage_level_date IS DISTINCT FROM EXCLUDED.coverage_level_date
            RETURNING id
        )
        SELECT id FROM upsert_condition

        UNION ALL

        SELECT id
        FROM conditions
        WHERE canonical_url = %(canonical_url)s
            AND version = %(version)s
            AND NOT EXISTS (SELECT 1 FROM upsert_condition)

        LIMIT 1
    """

    context_grouper_upsert_query = """
        INSERT INTO conditions_context_groupers (
            condition_id,
            name,
            category,
            canonical_url,
            code_count
        )
        VALUES (
            %(condition_id)s,
            %(name)s,
            %(category)s,
            %(canonical_url)s,
            %(code_count)s
        )
        ON CONFLICT (condition_id, canonical_url)
        DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            code_count = EXCLUDED.code_count
        WHERE
            conditions_context_groupers.name IS DISTINCT FROM EXCLUDED.name
            OR conditions_context_groupers.category IS DISTINCT FROM EXCLUDED.category
            OR conditions_context_groupers.code_count IS DISTINCT FROM EXCLUDED.code_count
    """
    condition_to_code_relationships: dict[
        ConditionUniqueIndex, ConditionToCodeRelationshipTrace
    ] = defaultdict()

    for item in processed:
        cond = item["condition"]
        cursor.execute(condition_upsert_query, cond)

        condition_canonical_url = cond.get("canonical_url")
        condition_version = cond.get("version")
        condition_name = cond.get("display_name")
        condition_index = (condition_canonical_url, condition_version)
        condition_payload = ConditionToCodeRelationshipTrace(
            condition_id=cond.get("id"),
            condition_display_name=condition_name,
            child_rsg_snomed_code_ids=[],
            version=condition_version,
        )

        condition_to_code_relationships[condition_index] = condition_payload

        groupers = item.get("context_groupers", [])
        if not groupers:
            continue

        grouper_params = [
            {
                "condition_id": cond.get("id"),
                "name": cg["name"],
                "category": cg["category"],
                "canonical_url": cg["canonical_url"],
                "code_count": cg["code_count"],
            }
            for cg in groupers
        ]

        cursor.executemany(context_grouper_upsert_query, grouper_params)

    return condition_to_code_relationships


def _insert_condition_to_child_rsg_relationships(
    cursor: Cursor, data: ConditionToCodeRelationshipIndex
) -> None:
    logger.info("⏳ Upserting code <> child RSG relationships...")
    relationship_upsert_query = """
        INSERT INTO condition_child_rsg_codes (
            condition_id,
            code_id
        )
        VALUES (
            %(condition_id)s,
            %(code_id)s
        )
        ON CONFLICT (condition_id, code_id) DO NOTHING
        RETURNING id
    """
    params = [
        {
            "condition_id": condition.get("condition_id"),
            "code_id": child_rsg_code_id,
        }
        for condition in data.values()
        for child_rsg_code_id in condition.get("child_rsg_snomed_code_ids", [])
    ]

    cursor.executemany(relationship_upsert_query, params)
    return


def _upsert_codes(cursor: Cursor, data: list[CodeRow]):
    """
    Upserts code rows.
    """

    logger.info("⏳ Upserting code records...")

    condition_upsert_query = """
        INSERT INTO codes (
            id,
            name,
            value,
            version,
            system_id
        )
        VALUES (
            %(id)s,
            %(name)s,
            %(value)s,
            %(version)s,
            %(system_id)s
        )
        ON CONFLICT (value, system_id, version)
        DO UPDATE SET
            name = EXCLUDED.name,
            value = EXCLUDED.value,
            version = EXCLUDED.version
        WHERE
            codes.name IS DISTINCT FROM EXCLUDED.name
            OR codes.value IS DISTINCT FROM EXCLUDED.value
            OR codes.version IS DISTINCT FROM EXCLUDED.version
        RETURNING id
    """

    params = [
        {
            "id": code.get("id"),
            "name": code.get("name"),
            "value": code.get("value"),
            "version": code.get("version"),
            "system_id": code.get("system_id"),
        }
        for code in data
    ]
    cursor.executemany(condition_upsert_query, params)


def _build_condition_groupers(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
) -> list[VsDict]:
    groupers = [vs for vs in valuesets_map.values() if is_condition_grouper(vs)]
    logger.info(f"🔎 Identified {len(groupers)} condition groupers to process.")
    return groupers


def _build_system_response(
    db_system_response: list[TupleRow | None],
) -> dict[SystemOid, SystemDbId]:
    response = defaultdict()
    for row in db_system_response:
        if row is None:
            continue

        response[row[0]] = row[1]

    if "Other" not in response.keys():
        raise ValueError("Fallback system other not found in db seeding")

    if SNOMED_OID not in response.keys():
        raise ValueError("SNOMED other not found in db seeding")

    return response


def load_system_data(
    cursor: Cursor,
) -> dict[SystemOid, SystemDbId]:
    """
    Loads system data into the data.

    New rows are inserted. Existing rows with the same oid, key, or
    are updated only when relevant fields have changed. This is done in a single transaction to systems data to ensure the insert either succeeds or fails all at once

    Args:
       cursor: A DB cursor
    """
    logger.info("⏳ Upserting system data...")

    # if we ever update this query to do conflict checks on other roles, we'll
    # need to update the trigger via a migration on when to fire an update to the
    #  updated_at column
    system_upsert_query = """
        MERGE INTO systems s
        USING (VALUES (
            %(key)s,
            %(display_name)s,
            %(oid)s
        )) as v(key, display_name, oid)
        ON s.key = v.key OR s.oid = v.oid

        WHEN MATCHED THEN
            UPDATE SET
                display_name = v.display_name,
                oid = v.oid
        WHEN NOT MATCHED THEN
            INSERT (
                key,
                display_name,
                oid
            )
            VALUES (v.key, v.display_name, v.oid)
        RETURNING s.oid, id;
    """

    params = [
        {
            "key": key,
            "oid": item["oid"],
            "display_name": item["display_name"],
        }
        for key, item in CODE_SYSTEM_DATA.items()
    ]

    cursor.executemany(system_upsert_query, params, returning=True)

    systems_response = [cursor.fetchone() for _ in cursor.results()]

    return _build_system_response(db_system_response=systems_response)


def load_tes_data(cursor: Cursor, system_data: dict[SystemOid, SystemDbId]) -> None:
    """
    Loads condition grouper data from the TES and upserts condition rows and their associated context grouper rows into the database.

    New rows are inserted. Existing rows with the same (canonical_url, version)
    are updated only when relevant fields have changed. This is done in a single transaction to systems data to ensure the insert either succeeds or fails all at once

    Args:
       cursor: A DB cursor
       system_data: inserted system data to be used by downstream code seeding
    """

    all_valuesets_map = load_valuesets_from_all_files()

    condition_groupers = _build_condition_groupers(valuesets_map=all_valuesets_map)

    processed = _build_processed_conditions(
        condition_groupers=condition_groupers,
        valuesets_map=all_valuesets_map,
    )

    if not processed:
        logger.info("⚠️  No conditions found to upsert.")
        return

    logger.info(f"⬆️  Total conditions to upsert: {len(processed)}")
    condition_to_code_relationships = _upsert_conditions_and_groupers(
        cursor=cursor, processed=processed
    )

    # seed codes, eventually this will replace the entirety
    # of the jsonb-forward functionality
    (rsg_codes, condition_to_code_relationships) = _build_rsg_codes(
        valuesets_map=all_valuesets_map,
        system_data=system_data,
        condition_to_code_relationships=condition_to_code_relationships,
        condition_groupers=condition_groupers,
    )
    _upsert_codes(cursor=cursor, data=rsg_codes)
    _insert_condition_to_child_rsg_relationships(
        cursor=cursor, data=condition_to_code_relationships
    )


def load_static_data(db_url: str, db_password: str) -> None:
    """
    Orchestration function that loads all static data into the DB.

    Args:
        db_url (str): The database URL
        db_password (str): The database password
    """
    start = time.perf_counter()

    try:
        with get_db_connection(db_url, db_password) as conn:
            with conn.cursor() as cursor:
                system_data = load_system_data(cursor=cursor)
                load_tes_data(cursor=cursor, system_data=system_data)

                logger.info("🏁 Done!")

    except Exception:
        logger.error(
            "❌ A critical error occurred during the static data upsert process.",
            exc_info=True,
        )
        logger.error("Make sure migrations have been run prior to seeding!")

    end = time.perf_counter()
    logger.info(f"⏱️  Static data loaded in {end - start:.3f} seconds")


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)

    db_url = os.getenv("DB_URL")
    db_password = os.getenv("DB_PASSWORD")

    if not db_url or not db_password:
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
    else:
        load_static_data(db_password=db_password, db_url=db_url)

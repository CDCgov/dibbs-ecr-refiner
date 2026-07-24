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
    FhirCodeTuple,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
    categorize_codes_by_system_oid,
    extract_codes_from_compose,
    get_child_rsg_valuesets,
    get_db_connection,
    get_sibling_context_valuesets,
    is_condition_grouper,
    load_valuesets_from_all_files,
    parse_child_rsg_details_from_use_context,
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

    canonical_url: str
    version: str
    display_name: str
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
    completeness: str | None


class ProcessedCondition(TypedDict):
    """
    A fully processed condition with its associated context grouper rows.
    """

    condition: ConditionRow
    context_groupers: list[ContextGrouperRow]


type SystemDbId = str
type SystemOid = str
type CodeVersion = str

type CodeValue = str
type SystemCodeTuple = tuple[SystemDbId, CodeVersion, CodeValue]


class ConditionToCodeRelationshipTrace(TypedDict):
    """
    A trace object to keep track of condition <> code relationships to seed the relevant join tables.
    """

    condition_id: UUID
    condition_display_name: str
    child_rsg_codes: set[SystemCodeTuple]
    non_child_rsg_codes: set[SystemCodeTuple]
    version: str


type ConditionUniqueIndex = tuple[VsCanonicalUrl, VsVersion]

type ConditionToCodeRelationshipIndex = dict[
    ConditionUniqueIndex, ConditionToCodeRelationshipTrace
]


class ProcessedCodePayload(TypedDict):
    """
    Information processed from the TES with information ready for database insertion.
    """

    condition_relationships: ConditionToCodeRelationshipIndex
    codes_to_insert: list[CodeRow]


def _upsert_tes_data(
    cursor: Cursor,
    versions: set[str],
) -> dict[str, UUID]:
    """
    Upserts TES rows based on distinct versions.

    Returns a mapping of version -> tes_id.
    """
    logger.info("⏳ Upserting TES records...")

    tes_upsert_query = """
        WITH upsert_tes AS (
            INSERT INTO tes (version)
            VALUES (%(version)s)
            ON CONFLICT (version) DO NOTHING
            RETURNING id
        )
        SELECT id FROM upsert_tes

        UNION ALL

        SELECT id FROM tes
        WHERE version = %(version)s
            AND NOT EXISTS (SELECT 1 FROM upsert_tes)

        LIMIT 1
    """

    version_to_tes_id: dict[str, UUID] = {}

    for version in versions:
        cursor.execute(tes_upsert_query, {"version": version})
        result = cursor.fetchone()

        if result is None or not result[0]:
            raise ValueError(f"TES upsert for version {version!r} did not return ID")

        version_to_tes_id[version] = result[0]

    logger.info(f"🛠️  Total TES rows upserted: {len(version_to_tes_id)}")
    return version_to_tes_id


def _build_codes(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
    condition_groupers: list[VsDict],
    oid_indexed_system_db_ids: dict[SystemOid, SystemDbId],
    condition_to_code_relationships: ConditionToCodeRelationshipIndex,
) -> ProcessedCodePayload:

    snomed_db_id = oid_indexed_system_db_ids[SNOMED_OID]
    codes_seen_so_far: set[tuple[str, str, str]] = set()
    codes_for_codes_table: list[CodeRow] = []

    for condition in condition_groupers:
        cond_canonical_url = condition.get("url", "")
        cond_version = condition.get("version", "")
        cond_index = (cond_canonical_url, cond_version)

        condition_child_rsg_snomed_codes: set[SystemCodeTuple] = set()
        condition_non_child_rsg_snomed_codes: set[SystemCodeTuple] = set()

        child_tuples: set[FhirCodeTuple] = set()

        for child_vs in get_child_rsg_valuesets(
            parent=condition, all_vs_map=valuesets_map
        ):
            if child_rsg_code := parse_snomed_from_url(child_vs.get("url", "")):
                display = parse_child_rsg_details_from_use_context(
                    child_vs.get("useContext", "")
                )
                code_index = (snomed_db_id, cond_version, child_rsg_code)
                if code_index not in codes_seen_so_far:
                    codes_seen_so_far.add(code_index)
                    code_row = CodeRow(
                        id=uuid4(),
                        code=child_rsg_code,
                        version=cond_version,
                        display=display,
                        system_id=snomed_db_id,
                    )
                    codes_for_codes_table.append(code_row)
                system_code_tuple = (
                    snomed_db_id,
                    cond_version,
                    child_rsg_code,
                )

                if system_code_tuple not in condition_child_rsg_snomed_codes:
                    condition_child_rsg_snomed_codes.add(system_code_tuple)

            child_codes = extract_codes_from_compose(child_vs)
            child_tuples.update(set(child_codes))

        condition_to_code_relationships[cond_index]["child_rsg_codes"] = (
            condition_child_rsg_snomed_codes
        )

        sibling_tuples = set()
        for sibling_vs in get_sibling_context_valuesets(condition, valuesets_map):
            sibling_tuples.update(extract_codes_from_compose(sibling_vs))

        all_tuples = sibling_tuples | child_tuples
        system_sorted_codes = categorize_codes_by_system_oid(set(all_tuples))

        for system_oid, code_list in system_sorted_codes.items():
            system_id = oid_indexed_system_db_ids.get(system_oid)
            if not system_id:
                continue

            for c in code_list:
                code = c.get("code")
                if not code:
                    continue

                code_index = (system_id, cond_version, code)
                if code_index not in codes_seen_so_far:
                    codes_seen_so_far.add(code_index)
                    code_row = CodeRow(
                        id=uuid4(),
                        code=code,
                        version=cond_version,
                        display=c.get("display") or "",
                        system_id=system_id,
                    )
                    codes_for_codes_table.append(code_row)
                system_code_tuple = (system_id, cond_version, code)
                if (
                    # skip code if already marked in child_rsgs so we don't try to
                    # upsert the same code twice in the same transaction and run into
                    # cardinality violations
                    system_code_tuple not in condition_child_rsg_snomed_codes
                    and system_code_tuple not in condition_non_child_rsg_snomed_codes
                ):
                    condition_non_child_rsg_snomed_codes.add(system_code_tuple)

        condition_to_code_relationships[cond_index]["non_child_rsg_codes"] = (
            condition_non_child_rsg_snomed_codes
        )

    return ProcessedCodePayload(
        codes_to_insert=codes_for_codes_table,
        condition_relationships=condition_to_code_relationships,
    )


def _build_processed_conditions(
    condition_groupers: list[VsDict],
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
    version_to_tes_id: dict[str, UUID],
) -> list[ProcessedCondition]:
    results: list[ProcessedCondition] = []

    for parent in condition_groupers:
        data = ConditionData(parent, valuesets_map)
        version = data.payload["version"]
        results.append(
            {
                "condition": {**data.payload, "tes_id": version_to_tes_id[version]},
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
                canonical_url,
                tes_id,
                display_name,
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
                %(canonical_url)s,
                %(tes_id)s,
                %(display_name)s,
                %(loinc_codes)s,
                %(snomed_codes)s,
                %(icd10_codes)s,
                %(rxnorm_codes)s,
                %(cvx_codes)s,
                %(coverage_level)s,
                %(coverage_level_reason)s,
                %(coverage_level_date)s
            )
            ON CONFLICT (canonical_url, tes_id)
            DO UPDATE SET
                display_name = EXCLUDED.display_name,
                loinc_codes = EXCLUDED.loinc_codes,
                snomed_codes = EXCLUDED.snomed_codes,
                icd10_codes = EXCLUDED.icd10_codes,
                rxnorm_codes = EXCLUDED.rxnorm_codes,
                cvx_codes = EXCLUDED.cvx_codes,
                coverage_level = EXCLUDED.coverage_level,
                coverage_level_reason = EXCLUDED.coverage_level_reason,
                coverage_level_date = EXCLUDED.coverage_level_date
            WHERE
                conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
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
        SELECT c.id
        FROM conditions c
        JOIN tes t ON t.id = c.tes_id
        WHERE c.canonical_url = %(canonical_url)s
            AND t.version = %(version)s
            AND NOT EXISTS (SELECT 1 FROM upsert_condition)
        LIMIT 1
    """

    context_grouper_upsert_query = """
        INSERT INTO conditions_context_groupers (
            condition_id,
            name,
            category,
            canonical_url,
            code_count,
            completeness
        )
        VALUES (
            %(condition_id)s,
            %(name)s,
            %(category)s,
            %(canonical_url)s,
            %(code_count)s,
            %(completeness)s
        )
        ON CONFLICT (condition_id, canonical_url)
        DO UPDATE SET
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            code_count = EXCLUDED.code_count,
            completeness = EXCLUDED.completeness
        WHERE
            conditions_context_groupers.name IS DISTINCT FROM EXCLUDED.name
            OR conditions_context_groupers.category IS DISTINCT FROM EXCLUDED.category
            OR conditions_context_groupers.code_count IS DISTINCT FROM EXCLUDED.code_count
            OR conditions_context_groupers.completeness IS DISTINCT FROM EXCLUDED.completeness
    """
    condition_to_code_relationships: dict[
        ConditionUniqueIndex, ConditionToCodeRelationshipTrace
    ] = defaultdict()

    for item in processed:
        cond = item["condition"]
        cursor.execute(condition_upsert_query, cond)
        condition_response = cursor.fetchone()

        if condition_response is None or not condition_response[0]:
            raise ValueError(
                f"Condition upsert for condition with params {cond} did not return ID"
            )

        cond_id = condition_response[0]
        condition_canonical_url = cond.get("canonical_url")
        condition_version = cond.get("version")
        condition_name = cond.get("display_name")
        condition_index = (condition_canonical_url, condition_version)
        condition_payload = ConditionToCodeRelationshipTrace(
            condition_id=cond_id,
            condition_display_name=condition_name,
            child_rsg_codes=set(),
            non_child_rsg_codes=set(),
            version=condition_version,
        )

        condition_to_code_relationships[condition_index] = condition_payload

        groupers = item.get("context_groupers", [])
        if not groupers:
            continue

        grouper_params = [
            {
                "condition_id": cond_id,
                "name": cg["name"],
                "category": cg["category"],
                "canonical_url": cg["canonical_url"],
                "code_count": cg["code_count"],
                "completeness": cg["completeness"],
            }
            for cg in groupers
        ]

        cursor.executemany(context_grouper_upsert_query, grouper_params)

    return condition_to_code_relationships


def _upsert_relationships(
    cursor: Cursor,
    condition_to_code_relationships: ConditionToCodeRelationshipIndex,
) -> None:
    logger.info("⏳ Refreshing relationships table...")

    cursor.execute("""
        CREATE TEMP TABLE IF NOT EXISTS stage_relationships (
            condition_id UUID NOT NULL,
            system_id UUID NOT NULL,
            version TEXT NOT NULL,
            code TEXT NOT NULL,
            is_child_rsg BOOLEAN NOT NULL
        ) ON COMMIT DROP
    """)
    cursor.execute("TRUNCATE stage_relationships")

    child_rsg_key = "child_rsg"
    non_child_rsg_key = "non_child_rsg"
    staged_counts = {child_rsg_key: 0, non_child_rsg_key: 0}

    def relationship_generator():
        for cond in condition_to_code_relationships.values():
            cond_id = cond["condition_id"]
            if not cond_id:
                continue

            for system_id, version, code in cond["child_rsg_codes"]:
                staged_counts[child_rsg_key] += 1
                yield (cond_id, system_id, version, code, True)

            for system_id, version, code in cond["non_child_rsg_codes"]:
                staged_counts[non_child_rsg_key] += 1
                yield (cond_id, system_id, version, code, False)

    logger.info("🚀 Streaming relationships into stage table...")
    with cursor.copy(
        """COPY stage_relationships (condition_id, system_id, version, code, is_child_rsg) FROM STDIN"""
    ) as copy:
        for row in relationship_generator():
            copy.write_row(row)

    cursor.execute("ANALYZE stage_relationships;")
    cursor.execute("TRUNCATE conditions_codes;")

    logger.info("🔗 Linking codes table to relationship joins...")

    cursor.execute("""
        INSERT INTO conditions_codes (condition_id, code_id, is_child_rsg)
        SELECT
            sr.condition_id,
            c.id AS code_id,
            sr.is_child_rsg
        FROM stage_relationships sr
        JOIN codes c
            ON  c.system_id = sr.system_id
            AND c.version = sr.version
            AND c.code = sr.code;
    """)

    inserted_count = cursor.rowcount
    logger.info(
        f"📥 Inserted {inserted_count:,} total relationships "
        f"({staged_counts[child_rsg_key]:,} child_rsg, {staged_counts[non_child_rsg_key]:,} non_child_rsg)."
    )

    cursor.execute("ANALYZE conditions_codes;")


def _upsert_codes(
    cursor: Cursor,
    data: ProcessedCodePayload,
) -> None:
    logger.info("⏳ Starting codes upsert process...")

    cursor.execute("""
        CREATE TEMP TABLE IF NOT EXISTS stage_codes (
            id UUID NOT NULL,
            system_id UUID NOT NULL,
            version TEXT NOT NULL,
            code TEXT NOT NULL,
            display TEXT
        ) ON COMMIT DROP
    """)
    cursor.execute("TRUNCATE stage_codes")

    def code_generator():
        for code in data["codes_to_insert"]:
            yield (
                code["id"],
                code["system_id"],
                code["version"],
                code["code"],
                code["display"],
            )

    logger.info("🚀 Streaming codes into stage table...")
    with cursor.copy(
        "COPY stage_codes (id, system_id, version, code, display) FROM STDIN"
    ) as copy:
        for record in code_generator():
            copy.write_row(record)

    logger.info(f"📥 Staged {len(data['codes_to_insert'])} unique code rows.")
    cursor.execute("ANALYZE stage_codes;")
    # bump up local memory to help with the large joins
    cursor.execute("SET LOCAL work_mem = '128MB'")

    cursor.execute("""
        INSERT INTO codes (id, system_id, version, code, display)
        SELECT s.id, s.system_id, s.version, s.code, s.display
        FROM stage_codes s
        LEFT JOIN codes c
            ON  s.system_id = c.system_id
            AND s.code = c.code
            AND s.version = c.version
        WHERE c.id IS NULL
        ORDER BY s.system_id, s.version, s.code
        ON CONFLICT (system_id, version, code) DO NOTHING;
    """)

    logger.info(f"✨ {cursor.rowcount:,} total new rows inserted in codes table.")


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

    distinct_versions = {vs.get("version", "") for vs in condition_groupers}
    version_to_tes_id = _upsert_tes_data(cursor=cursor, versions=distinct_versions)

    processed = _build_processed_conditions(
        condition_groupers=condition_groupers,
        valuesets_map=all_valuesets_map,
        version_to_tes_id=version_to_tes_id,
    )

    if not processed:
        logger.info("⚠️  No conditions found to upsert.")
        return

    logger.info(f"⬆️  Total conditions to upsert: {len(processed)}")
    condition_to_code_relationships = _upsert_conditions_and_groupers(
        cursor=cursor,
        processed=processed,
    )

    # # seed codes, eventually this will replace the entirety
    # # of the jsonb-forward functionality
    condition_to_code_relationships = _build_codes(
        valuesets_map=all_valuesets_map,
        oid_indexed_system_db_ids=system_data,
        condition_to_code_relationships=condition_to_code_relationships,
        condition_groupers=condition_groupers,
    )

    _upsert_codes(cursor=cursor, data=condition_to_code_relationships)

    _upsert_relationships(
        cursor=cursor,
        condition_to_code_relationships=condition_to_code_relationships[
            "condition_relationships"
        ],
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

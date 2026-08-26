import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
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
    categorize_codes_by_system_oid,
    extract_codes_from_compose,
    get_child_rsg_valuesets,
    get_db_connection,
    get_sibling_context_valuesets,
    is_condition_grouper,
    load_valuesets_from_all_files,
    map_coverage_level_to_acg_completeness,
    parse_child_rsg_details_from_use_context,
    parse_snomed_from_url,
    parse_valueset_category,
    parse_valueset_source_name,
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


class ValuesetRow(TypedDict):
    """
    A context grouper row to upsert into the DB.
    """

    condition_version: str
    canonical_url: str
    parent_url: str
    display_name: str
    code_count: int
    category: str | None
    completeness: str | None


class ProcessedCondition(TypedDict):
    """
    A fully processed condition with its associated context grouper rows.
    """

    condition: ConditionRow
    context_groupers: list[ContextGrouperRow]


@dataclass(frozen=True)
class ConditionsCodesTrace:
    """
    Trace info to insert into the condition <> code relationships join tables.
    """

    system_db_id: UUID
    code: str
    valueset_url: str


class ConditionToCodeToValuesetTrace(TypedDict):
    """
    A trace object to keep track of condition <> code relationships to seed the relevant join tables.
    """

    condition_id: UUID
    condition_url: str
    valueset_urls: list[str]
    condition_display_name: str
    child_rsg_codes: set[ConditionsCodesTrace]
    non_child_rsg_codes: set[ConditionsCodesTrace]


type SystemDbId = UUID
type SystemOid = str
type SystemOidToDbIdMap = dict[SystemOid, SystemDbId]
type ConditionUniqueIndex = tuple[VsCanonicalUrl, VsVersion]

type RelationshipsToInsert = dict[ConditionUniqueIndex, ConditionToCodeToValuesetTrace]


class ProcessedCodePayload(TypedDict):
    """
    Information processed from the TES with information ready for database insertion.
    """

    condition_relationships: RelationshipsToInsert
    codes_to_insert: list[CodeRow]
    valuesets_to_insert: list[ValuesetRow]


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


type CodeValue = str
type CodedConceptUniqueKey = tuple[SystemDbId, CodeValue]


@dataclass
class BuildCodeContext:
    """
    Context for code and code relationships that .
    """

    db_ids: SystemOidToDbIdMap
    unique_codes: dict[tuple[UUID, str], CodeRow] = field(default_factory=dict)
    unique_valuesets: dict[tuple[str, str, str], ValuesetRow] = field(
        default_factory=dict
    )

    def mark_code_as_seen(
        self,
        code_trace: ConditionsCodesTrace,
        code: str,
        display: str,
        valueset_url: str,
    ):
        """Tracks trace and registers code row information across build functions."""

        system_code_tuple = (code_trace.system_db_id, code)
        if system_code_tuple in self.unique_codes.keys():
            return False

        self.unique_codes[system_code_tuple] = CodeRow(
            id=uuid4(),
            code=code,
            display=display,
            system_id=str(code_trace.system_db_id),
            valueset_url=valueset_url,
        )

        return True

    def mark_valueset_as_seen(
        self, valueset: VsDict, condition_url: str, condition_version: str
    ):
        """Tracks trace and registers valueset information across build functions."""
        url = valueset.get("url", "")
        valueset_key = (condition_url, condition_version, url)

        if not url or valueset_key in self.unique_valuesets.keys():
            return False

        name = parse_valueset_source_name(valueset)

        # TODO: should we also include the parent condition groupers in the
        # table that map into the conditions?
        self.unique_valuesets[valueset_key] = ValuesetRow(
            canonical_url=url,
            condition_version=condition_version,
            parent_url=condition_url,
            display_name=name,
            category=parse_valueset_category(name),
            code_count=len(extract_codes_from_compose(valueset)),
            completeness=map_coverage_level_to_acg_completeness(valueset),
        )
        return True


def _build_child_codes(
    child_valuesets: list[VsDict],
    code_context: BuildCodeContext,
    condition_grouper_url: str,
    condition_version: str,
) -> tuple[set[ConditionsCodesTrace], list[VsDict]]:
    snomed_db_id = code_context.db_ids[SNOMED_OID]
    condition_child_rsg_snomed_codes: set[ConditionsCodesTrace] = set()
    child_vs_list: list[VsDict] = []

    for child_vs in child_valuesets:
        code_context.mark_valueset_as_seen(
            valueset=child_vs,
            condition_url=condition_grouper_url,
            condition_version=condition_version,
        )

        source_url = child_vs.get("url", "")
        child_rsg_code = parse_snomed_from_url(source_url)

        if not child_rsg_code:
            continue
        child_vs_list.append(child_vs)

        display = parse_child_rsg_details_from_use_context(
            child_vs.get("useContext", "")
        )
        code_trace = ConditionsCodesTrace(
            system_db_id=snomed_db_id,
            code=child_rsg_code,
            valueset_url=source_url,
        )
        code_context.mark_code_as_seen(
            code_trace=code_trace,
            code=child_rsg_code,
            display=display,
            valueset_url=source_url,
        )

        condition_child_rsg_snomed_codes.add(code_trace)

    return condition_child_rsg_snomed_codes, child_vs_list


def _build_sibling_codes(
    condition_valuesets: list[VsDict],
    code_context: BuildCodeContext,
    condition_snomed_child_rsgs: set[ConditionsCodesTrace],
    condition_grouper_url: str,
    condition_version: str,
) -> set[ConditionsCodesTrace]:
    condition_non_child_rsg_snomed_codes: set[ConditionsCodesTrace] = set()

    for vs in condition_valuesets:
        code_context.mark_valueset_as_seen(
            valueset=vs,
            condition_url=condition_grouper_url,
            condition_version=condition_version,
        )

        system_sorted_codes = categorize_codes_by_system_oid(
            extract_codes_from_compose(vs)
        )

        for system_oid, code_list in system_sorted_codes.items():
            system_id = code_context.db_ids.get(system_oid)
            if not system_id:
                continue

            for c in code_list:
                code = c.code
                source_url = c.source_url
                source_name = c.source_name
                if not code or not source_url or not source_name:
                    continue

                code_trace = ConditionsCodesTrace(
                    system_db_id=system_id,
                    code=code,
                    valueset_url=source_url,
                )

                code_context.mark_code_as_seen(
                    code_trace,
                    code,
                    c.display or "",
                    valueset_url=source_url,
                )

                if code_trace not in condition_snomed_child_rsgs:
                    # skip code if already marked in child_rsgs so we don't try to
                    # upsert the same code twice in the same transaction and run into
                    # cardinality violations
                    condition_non_child_rsg_snomed_codes.add(code_trace)

    return condition_non_child_rsg_snomed_codes


def _build_codes(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
    condition_groupers: list[VsDict],
    oid_indexed_system_db_ids: SystemOidToDbIdMap,
    condition_to_code_relationships: RelationshipsToInsert,
) -> ProcessedCodePayload:
    code_context = BuildCodeContext(db_ids=oid_indexed_system_db_ids)

    for condition in condition_groupers:
        cond_canonical_url = condition.get("url", "")
        cond_version = condition.get("version", "")

        if not cond_canonical_url or not cond_version:
            continue

        cond_key = (cond_canonical_url, cond_version)

        condition_child_rsg_snomed_codes, child_valuesets = _build_child_codes(
            child_valuesets=get_child_rsg_valuesets(
                parent=condition, all_vs_map=valuesets_map
            ),
            code_context=code_context,
            condition_grouper_url=cond_canonical_url,
            condition_version=cond_version,
        )

        condition_to_code_relationships[cond_key]["child_rsg_codes"].update(
            condition_child_rsg_snomed_codes
        )

        # build all codes we need from sibling valuesets
        sibling_valuesets = get_sibling_context_valuesets(condition, valuesets_map)
        sibling_valuesets.extend(child_valuesets)

        condition_non_child_rsg_snomed_codes = _build_sibling_codes(
            condition_valuesets=sibling_valuesets,
            code_context=code_context,
            condition_snomed_child_rsgs=condition_child_rsg_snomed_codes,
            condition_grouper_url=cond_canonical_url,
            condition_version=cond_version,
        )

        condition_to_code_relationships[cond_key]["non_child_rsg_codes"].update(
            condition_non_child_rsg_snomed_codes
        )

    return ProcessedCodePayload(
        codes_to_insert=list(code_context.unique_codes.values()),
        valuesets_to_insert=list(code_context.unique_valuesets.values()),
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


def _upsert_conditions(
    cursor: Cursor,
    processed: list[ProcessedCondition],
) -> RelationshipsToInsert:
    """
    Upserts condition rows and their associated context grouper rows.

    Each condition is upserted using a CTE that returns the row's id
    regardless of whether the row was inserted, updated, or unchanged.

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
                coverage_level,
                coverage_level_reason,
                coverage_level_date
            )
            VALUES (
                %(canonical_url)s,
                %(tes_id)s,
                %(display_name)s,
                %(coverage_level)s,
                %(coverage_level_reason)s,
                %(coverage_level_date)s
            )
            ON CONFLICT (canonical_url, tes_id)
            DO UPDATE SET
                display_name = EXCLUDED.display_name,
                coverage_level = EXCLUDED.coverage_level,
                coverage_level_reason = EXCLUDED.coverage_level_reason,
                coverage_level_date = EXCLUDED.coverage_level_date
            WHERE
                conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
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

    condition_to_code_relationships: dict[
        ConditionUniqueIndex, ConditionToCodeToValuesetTrace
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

        condition_payload = ConditionToCodeToValuesetTrace(
            condition_id=cond_id,
            condition_display_name=condition_name,
            valueset_urls=[],
            child_rsg_codes=set(),
            non_child_rsg_codes=set(),
            condition_url=condition_canonical_url,
        )

        condition_to_code_relationships[
            (condition_canonical_url, condition_version)
        ] = condition_payload

    return condition_to_code_relationships


def _upsert_relationships(
    cursor: Cursor,
    condition_to_code_relationships: RelationshipsToInsert,
) -> None:
    cursor.execute("SELECT condition_id, canonical_url, id FROM valuesets;")
    valueset_map = {(row[0], row[1]): row[2] for row in cursor.fetchall()}

    cursor.execute("SELECT system_id, code, id FROM codes;")
    code_map = {(row[0], row[1]): row[2] for row in cursor.fetchall()}

    logger.info("⏳ Refreshing relationships table...")
    cursor.execute("TRUNCATE conditions_codes_temp;")

    child_rsg_key = "child_rsg"
    non_child_rsg_key = "non_child_rsg"
    staged_counts = {child_rsg_key: 0, non_child_rsg_key: 0}

    def relationship_generator():
        for cond in condition_to_code_relationships.values():
            cond_id = cond["condition_id"]
            if not cond_id:
                continue

            for code in cond["child_rsg_codes"]:
                # Pass the tuple (cond_id, canonical_url) to get the exact valueset
                code_id = code_map.get((code.system_db_id, code.code))
                valueset_id = valueset_map.get((cond_id, code.valueset_url))

                if not code_id or not valueset_id:
                    continue

                staged_counts[child_rsg_key] += 1
                yield (cond_id, code_id, True, valueset_id)

            for code in cond["non_child_rsg_codes"]:
                code_id = code_map.get((code.system_db_id, code.code))
                valueset_id = valueset_map.get((cond_id, code.valueset_url))

                if not code_id or not valueset_id:
                    continue

                staged_counts[non_child_rsg_key] += 1
                yield (cond_id, code_id, False, valueset_id)

    logger.info("🚀 Streaming relationships into conditions_codes table...")
    with cursor.copy(
        "COPY conditions_codes_temp (condition_id, code_id, is_child_rsg, valueset_id) FROM STDIN"
    ) as copy:
        for row in relationship_generator():
            copy.write_row(row)

    inserted_count = sum(staged_counts.values())
    logger.info(
        f"📥 Inserted {inserted_count:,} total relationships "
        f"(unique counts: {staged_counts[child_rsg_key]:,} child_rsg, {staged_counts[non_child_rsg_key]:,} non_child_rsg)."
    )

    cursor.execute("ANALYZE conditions_codes_temp;")
    return


def _upsert_codes(
    cursor: Cursor,
    data: list[CodeRow],
) -> None:
    logger.info("⏳ Starting codes upsert process...")

    cursor.execute("""
        CREATE TEMP TABLE IF NOT EXISTS stage_codes (
            id UUID NOT NULL,
            system_id UUID NOT NULL,
            code TEXT NOT NULL,
            display TEXT
        ) ON COMMIT DROP
    """)
    cursor.execute("TRUNCATE stage_codes")

    def code_generator():
        for code in data:
            yield (
                code["id"],
                code["system_id"],
                code["code"],
                code["display"],
            )

    logger.info("🚀 Streaming codes into stage table...")
    with cursor.copy(
        "COPY stage_codes (id, system_id, code, display) FROM STDIN"
    ) as copy:
        for record in code_generator():
            copy.write_row(record)

    logger.info(f"📥 Staged {len(data)} unique code rows.")
    cursor.execute("ANALYZE stage_codes;")

    cursor.execute("""
        INSERT INTO codes (id, system_id, code, display)
        SELECT s.id, s.system_id, s.code, s.display
        FROM stage_codes s
        LEFT JOIN codes c
            ON  s.system_id = c.system_id
            AND s.code = c.code
        WHERE c.id IS NULL
        ON CONFLICT (system_id, code) DO NOTHING;
    """)

    logger.info(f"✨ {cursor.rowcount:,} total new rows inserted in codes table.")
    return


def _upsert_valuesets(
    cursor: Cursor,
    data: list[ValuesetRow],
) -> None:
    logger.info("⏳ Starting valuesets upsert process...")

    cursor.execute("""
        CREATE TEMP TABLE IF NOT EXISTS stage_valuesets (
            display_name TEXT,
            category TEXT,
            canonical_url TEXT NOT NULL,
            code_count INT,
            completeness TEXT,
            parent_url TEXT NOT NULL,
            version TEXT NOT NULL
        ) ON COMMIT DROP
    """)
    cursor.execute("TRUNCATE stage_valuesets")

    def valueset_generator():
        for v in data:
            yield (
                v["display_name"],
                v["category"],
                v["canonical_url"],
                v["code_count"],
                v["completeness"],
                v["parent_url"],
                v["condition_version"],
            )

    logger.info("🚀 Streaming valuesets into stage table...")
    with cursor.copy(
        "COPY stage_valuesets (display_name, category, canonical_url, code_count, completeness, parent_url, version) FROM STDIN"
    ) as copy:
        for record in valueset_generator():
            copy.write_row(record)

    logger.info(f"📥 Staged {len(data)} unique valueset rows.")
    cursor.execute("ANALYZE stage_valuesets;")

    cursor.execute("""
    INSERT INTO valuesets (
        condition_id,
        display_name,
        category,
        canonical_url,
        code_count,
        completeness,
        parent_url
    )
    SELECT
        c.id,
        s.display_name,
        s.category,
        s.canonical_url,
        s.code_count,
        s.completeness,
        s.parent_url
    FROM stage_valuesets s
    INNER JOIN conditions c ON s.parent_url = c.canonical_url
    INNER JOIN tes t ON t.id = c.tes_id AND s.version = t.version
    ON CONFLICT (condition_id, canonical_url)
    DO UPDATE SET
        display_name = EXCLUDED.display_name,
        category     = EXCLUDED.category,
        code_count   = EXCLUDED.code_count,
        completeness = EXCLUDED.completeness,
        parent_url   = EXCLUDED.parent_url
    WHERE
        valuesets.display_name IS DISTINCT FROM EXCLUDED.display_name
        OR valuesets.category IS DISTINCT FROM EXCLUDED.category
        OR valuesets.code_count IS DISTINCT FROM EXCLUDED.code_count
        OR valuesets.completeness IS DISTINCT FROM EXCLUDED.completeness
        OR valuesets.parent_url IS DISTINCT FROM EXCLUDED.parent_url;
    """)

    logger.info(
        f"✨ {cursor.rowcount:,} new valuesets rows inserted into the valuesets table."
    )
    return


def _build_condition_groupers(
    valuesets_map: dict[tuple[VsCanonicalUrl, VsVersion], VsDict],
) -> list[VsDict]:
    groupers = [vs for vs in valuesets_map.values() if is_condition_grouper(vs)]
    logger.info(f"🔎 Identified {len(groupers)} condition groupers to process.")
    return groupers


def _build_system_response(
    db_system_response: list[TupleRow | None],
) -> SystemOidToDbIdMap:
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


def load_system_data(cursor: Cursor) -> dict[SystemOid, UUID]:
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


def load_tes_data(
    cursor: Cursor, system_data: dict[SystemOid, UUID], seed_all_tes_data=False
) -> None:
    """
    Loads condition grouper data from the TES and upserts condition rows and their associated context grouper rows into the database.

    New rows are inserted. Existing rows with the same (canonical_url, version)
    are updated only when relevant fields have changed. This is done in a single transaction to systems data to ensure the insert either succeeds or fails all at once

    Args:
       cursor: A DB cursor
       system_data: inserted system data to be used by downstream code seeding
       seed_all_tes_data: flag for whether to seed all available TES values
    """
    all_valuesets_map = load_valuesets_from_all_files(
        seed_all_tes_data=seed_all_tes_data
    )

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
    condition_to_code_relationships = _upsert_conditions(
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

    _upsert_valuesets(
        cursor=cursor, data=condition_to_code_relationships["valuesets_to_insert"]
    )

    _upsert_codes(
        cursor=cursor, data=condition_to_code_relationships["codes_to_insert"]
    )

    _upsert_relationships(
        cursor=cursor,
        condition_to_code_relationships=condition_to_code_relationships[
            "condition_relationships"
        ],
    )


def load_static_data(db_url: str, db_password: str, seed_all_tes_data: bool) -> None:
    """
    Orchestration function that loads all static data into the DB.

    Args:
        db_url (str): The database URL
        db_password (str): The database password
        seed_all_tes_data (str): Whether to seed all TES data or not
    """
    start = time.perf_counter()

    try:
        with get_db_connection(db_url, db_password) as conn:
            with conn.cursor() as cursor:
                system_data = load_system_data(cursor=cursor)
                load_tes_data(
                    cursor=cursor,
                    system_data=system_data,
                    seed_all_tes_data=seed_all_tes_data,
                )

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

    seed_all_tes_data = os.getenv("SEED_ALL_TES_DATA")
    env = os.getenv("ENV")
    seed_all = seed_all_tes_data == "true" if seed_all_tes_data else env != "local"

    db_url = os.getenv("DB_URL")
    db_password = os.getenv("DB_PASSWORD")

    if not db_url or not db_password:
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
    else:
        load_static_data(
            db_password=db_password,
            db_url=db_url,
            seed_all_tes_data=seed_all,
        )

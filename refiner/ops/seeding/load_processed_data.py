"""
Seed the database from the processed TES tables.

Reads the gzipped CSV that `tes/normalize` produced and loads it into Postgres.
Nothing here understands FHIR: the version-specific unpacking happened once, at
normalize time, and this step only moves flat rows.

The shape is COPY into an unlogged stage table, then `INSERT ... SELECT` with
`ON CONFLICT` into the real one. Because the stage tables carry the natural keys
(canonical urls, versions, code system OIDs), the foreign keys are resolved by
joining rather than by round-tripping generated ids back into Python--which is
what the previous loader spent most of its time doing.

Every stage column is TEXT and cast on the way in, so a malformed value fails on
a cast with the row in hand rather than inside COPY.
"""

import gzip
import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path

from connection import get_db_connection
from dotenv import load_dotenv
from psycopg import Cursor
from systems import upsert_systems

logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent.parent / "tes" / "data" / "processed"


@contextmanager
def _timed(label: str):
    """
    Log how long a load phase took, so a regression is attributable.
    """

    start = time.perf_counter()
    yield
    logger.info(f"⏱️  {label}: {time.perf_counter() - start:.1f}s")


# how many TES releases to keep when not seeding everything; local and CI work
# only ever compare the current release against the one before it
DEFAULT_VERSIONS_TO_KEEP = 2

STAGE_TABLES: dict[str, tuple[str, ...]] = {
    "stage_conditions": (
        "canonical_url",
        "version",
        "display_name",
        "coverage_level",
        "coverage_level_reason",
        "coverage_level_date",
    ),
    "stage_valuesets": (
        "condition_url",
        "condition_version",
        "canonical_url",
        "display_name",
        "category",
        "code_count",
        "completeness",
    ),
    "stage_codes": ("system_oid", "code", "display"),
    "stage_memberships": (
        "condition_url",
        "condition_version",
        "valueset_url",
        "system_oid",
        "code",
        "is_child_rsg",
        "is_trigger_code",
    ),
}

# (constraint name, local column, referenced table) -- must match the schema in
# refiner/migrations; dropped and restored around the bulk load below
FOREIGN_KEYS = (
    ("fk_code_id_fkey", "code_id", "codes"),
    ("fk_condition_id_fkey", "condition_id", "conditions"),
    ("fk_valueset_id_fkey", "valueset_id", "valuesets"),
)

SOURCE_FILES = {
    "stage_conditions": "conditions.csv.gz",
    "stage_valuesets": "valuesets.csv.gz",
    "stage_codes": "codes.csv.gz",
    "stage_memberships": "memberships.csv.gz",
}


def _stage(cursor: Cursor, table: str, path: Path) -> int:
    """
    COPY one gzipped CSV into an unlogged stage table.

    The file is streamed to the server as bytes rather than parsed in Python --
    the header line is consumed by COPY itself.

    Args:
        cursor: A database cursor.
        table: Stage table to create and fill.
        path: The `.csv.gz` to read.

    Returns:
        Number of rows staged.
    """

    columns = STAGE_TABLES[table]
    definition = ", ".join(f"{column} TEXT" for column in columns)

    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute(f"CREATE UNLOGGED TABLE {table} ({definition})")

    statement = (
        f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    )
    with cursor.copy(statement) as copy, gzip.open(path, "rb") as handle:
        while chunk := handle.read(1 << 20):
            copy.write(chunk)

    cursor.execute(f"ANALYZE {table}")
    cursor.execute(f"SELECT count(*) FROM {table}")
    row = cursor.fetchone()
    return row[0] if row else 0


def _versions_to_seed(cursor: Cursor, seed_all: bool, keep: int) -> list[str]:
    """
    Decide which TES releases to project into the database.

    Versions are ordered numerically rather than lexically so a future 10.0.0
    sorts above 9.0.0.

    Args:
        cursor: A database cursor.
        seed_all: Whether to seed every release present in the processed data.
        keep: How many of the newest releases to seed when `seed_all` is False.

    Returns:
        The version strings to seed, newest first.
    """

    cursor.execute("""
        SELECT version
        FROM stage_conditions
        GROUP BY version
        ORDER BY string_to_array(version, '.')::int[] DESC
    """)
    versions = [row[0] for row in cursor.fetchall()]
    return versions if seed_all else versions[:keep]


def _reject_partial_seed_over_fuller_database(
    cursor: Cursor, versions: list[str]
) -> None:
    """
    Refuse a seed that would strand releases already in the database.

    `_refresh_memberships` truncates the whole junction and refills only the
    versions being seeded, so a run whose window is narrower than what the
    database already holds silently leaves every other release with conditions
    and valuesets but no codes. Those conditions stay configurable in the UI and
    activate to an `active.json` that matches nothing.

    This is never something anyone means to do: production seeds every release,
    local and CI seed two against a database they just wiped, and the only way to
    cross them is pointing a local-mode run at a restored production dump --
    exactly the case where the stranded releases still have configurations
    pinned to them.

    Args:
        cursor: A database cursor.
        versions: The releases this run is about to seed.

    Raises:
        SystemExit: The database holds releases this run would strand.
    """

    cursor.execute("SELECT version FROM tes")
    stranded = {row[0] for row in cursor.fetchall()} - set(versions)
    if not stranded:
        return

    raise SystemExit(
        f"Refusing to seed {sorted(versions)} over a database that also holds "
        f"{sorted(stranded)}: those releases would keep their conditions but "
        "lose every code. Re-run with SEED_ALL_TES_DATA=true, or start from a "
        "clean database with `just db refresh`."
    )


def _upsert_tes_versions(cursor: Cursor, versions: list[str]) -> None:
    """
    Ensure a `tes` row exists for every release being seeded.
    """

    cursor.executemany(
        "INSERT INTO tes (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
        [(version,) for version in versions],
    )
    logger.info(f"🛠️  TES releases seeded: {', '.join(versions)}")


def _upsert_conditions(cursor: Cursor, versions: list[str]) -> None:
    """
    Project staged condition rows, joining each to its TES release.
    """

    cursor.execute(
        """
        INSERT INTO conditions (
            canonical_url, tes_id, display_name,
            coverage_level, coverage_level_reason, coverage_level_date
        )
        SELECT
            s.canonical_url,
            t.id,
            NULLIF(s.display_name, ''),
            NULLIF(s.coverage_level, ''),
            NULLIF(s.coverage_level_reason, ''),
            NULLIF(s.coverage_level_date, '')::date
        FROM stage_conditions s
        JOIN tes t ON t.version = s.version
        WHERE s.version = ANY(%(versions)s)
        ON CONFLICT (canonical_url, tes_id) DO UPDATE SET
            display_name          = EXCLUDED.display_name,
            coverage_level        = EXCLUDED.coverage_level,
            coverage_level_reason = EXCLUDED.coverage_level_reason,
            coverage_level_date   = EXCLUDED.coverage_level_date
        WHERE conditions.display_name IS DISTINCT FROM EXCLUDED.display_name
           OR conditions.coverage_level IS DISTINCT FROM EXCLUDED.coverage_level
           OR conditions.coverage_level_reason IS DISTINCT FROM EXCLUDED.coverage_level_reason
           OR conditions.coverage_level_date IS DISTINCT FROM EXCLUDED.coverage_level_date
        """,
        {"versions": versions},
    )
    logger.info(f"✨ {cursor.rowcount:,} condition rows inserted or updated.")


def _upsert_valuesets(cursor: Cursor, versions: list[str]) -> None:
    """
    Project staged leaf groupers, resolving each to its condition row.
    """

    cursor.execute(
        """
        INSERT INTO valuesets (
            condition_id, display_name, category, canonical_url,
            code_count, completeness, parent_url
        )
        SELECT
            c.id,
            NULLIF(s.display_name, ''),
            s.category,
            s.canonical_url,
            s.code_count::int,
            NULLIF(s.completeness, ''),
            s.condition_url
        FROM stage_valuesets s
        JOIN tes t ON t.version = s.condition_version
        JOIN conditions c ON c.canonical_url = s.condition_url AND c.tes_id = t.id
        WHERE s.condition_version = ANY(%(versions)s)
        ON CONFLICT (condition_id, canonical_url) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            category     = EXCLUDED.category,
            code_count   = EXCLUDED.code_count,
            completeness = EXCLUDED.completeness,
            parent_url   = EXCLUDED.parent_url
        WHERE valuesets.display_name IS DISTINCT FROM EXCLUDED.display_name
           OR valuesets.category IS DISTINCT FROM EXCLUDED.category
           OR valuesets.code_count IS DISTINCT FROM EXCLUDED.code_count
           OR valuesets.completeness IS DISTINCT FROM EXCLUDED.completeness
           OR valuesets.parent_url IS DISTINCT FROM EXCLUDED.parent_url
        """,
        {"versions": versions},
    )
    logger.info(f"✨ {cursor.rowcount:,} valueset rows inserted or updated.")


def _upsert_codes(cursor: Cursor, versions: list[str]) -> None:
    """
    Project the codes actually referenced by the releases being seeded.

    `codes.csv.gz` covers every release, so it is narrowed to the memberships in
    scope rather than loading codes no seeded condition points at.
    """

    cursor.execute(
        """
        INSERT INTO codes (system_id, code, display)
        SELECT DISTINCT sys.id, s.code, s.display
        FROM stage_codes s
        JOIN systems sys ON sys.oid = s.system_oid
        WHERE EXISTS (
            SELECT 1 FROM stage_memberships m
            WHERE m.system_oid = s.system_oid
              AND m.code = s.code
              AND m.condition_version = ANY(%(versions)s)
        )
        ON CONFLICT (system_id, code) DO NOTHING
        """,
        {"versions": versions},
    )
    logger.info(f"✨ {cursor.rowcount:,} code rows inserted.")


def _refresh_memberships(cursor: Cursor, versions: list[str]) -> None:
    """
    Rebuild the condition/code/valueset junction.

    Truncate-and-rebuild rather than upsert: the junction is a pure projection
    of the processed data, and a membership that disappears upstream has to
    disappear here too.
    """

    logger.info("⏳ Refreshing relationships table...")
    cursor.execute("TRUNCATE conditions_codes_temp")

    # three per-row foreign key checks across a million rows cost ~38s; dropping
    # the constraints and re-adding them validates the whole table in one pass
    # instead, for ~0.3s. safe because this runs inside the loader's single
    # transaction--DDL is transactional in postgres, so a failure anywhere
    # rolls the constraints back with the data--and because every id inserted
    # below came from joining against the very tables being referenced.
    for constraint, _, _ in FOREIGN_KEYS:
        cursor.execute(
            f"ALTER TABLE conditions_codes_temp DROP CONSTRAINT {constraint}"
        )

    cursor.execute(
        """
        INSERT INTO conditions_codes_temp (
            condition_id, code_id, valueset_id, is_child_rsg, is_trigger_code
        )
        SELECT c.id, co.id, v.id,
               m.is_child_rsg::boolean,
               m.is_trigger_code::boolean
        FROM stage_memberships m
        JOIN tes t ON t.version = m.condition_version
        JOIN conditions c ON c.canonical_url = m.condition_url AND c.tes_id = t.id
        JOIN valuesets v ON v.condition_id = c.id AND v.canonical_url = m.valueset_url
        JOIN systems sys ON sys.oid = m.system_oid
        JOIN codes co ON co.system_id = sys.id AND co.code = m.code
        WHERE m.condition_version = ANY(%(versions)s)
        """,
        {"versions": versions},
    )
    inserted = cursor.rowcount

    for constraint, column, table in FOREIGN_KEYS:
        cursor.execute(
            f"ALTER TABLE conditions_codes_temp ADD CONSTRAINT {constraint} "
            f"FOREIGN KEY ({column}) REFERENCES {table}(id) ON DELETE CASCADE"
        )

    cursor.execute("ANALYZE conditions_codes_temp")

    cursor.execute(
        """
        SELECT count(*) FILTER (WHERE is_child_rsg),
               count(*) FILTER (WHERE is_trigger_code)
        FROM conditions_codes_temp
        """
    )
    child_rsg, trigger = cursor.fetchone() or (0, 0)
    logger.info(
        f"📥 Inserted {inserted:,} total relationships "
        f"({child_rsg:,} child_rsg, {trigger:,} trigger_code)."
    )

    _warn_on_dropped_memberships(cursor, versions, inserted)


def _warn_on_dropped_memberships(
    cursor: Cursor, versions: list[str], inserted: int
) -> None:
    """
    Report staged memberships that no join could resolve.

    A non-zero count means the processed tables are internally inconsistent --
    a membership naming a valueset or code that no other file declares -- which
    is a normalize bug, not a data condition.
    """

    cursor.execute(
        "SELECT count(*) FROM stage_memberships WHERE condition_version = ANY(%(versions)s)",
        {"versions": versions},
    )
    row = cursor.fetchone()
    staged = row[0] if row else 0

    if staged != inserted:
        logger.warning(
            f"⚠️ {staged - inserted:,} staged memberships did not resolve to a "
            "condition, valueset, and code. The processed tables disagree with "
            "each other; re-run normalize."
        )


def load_processed_data(
    db_url: str, db_password: str, seed_all: bool, processed_dir: Path = PROCESSED_DIR
) -> None:
    """
    Load the processed TES tables into the database.

    Args:
        db_url: PostgreSQL connection URL.
        db_password: Password for that connection.
        seed_all: Seed every release rather than only the newest few.
        processed_dir: Directory holding the processed CSV and manifest.
    """

    start = time.perf_counter()

    with get_db_connection(db_url, db_password) as connection:
        with connection.cursor() as cursor:
            upsert_systems(cursor=cursor)

            for table, filename in SOURCE_FILES.items():
                path = processed_dir / filename
                if not path.exists():
                    raise FileNotFoundError(
                        f"{path} not found. Run `just tes normalize` to build the "
                        "processed tables before seeding."
                    )
                with _timed(f"stage {filename}"):
                    staged = _stage(cursor, table, path)
                logger.info(f"📥 Staged {staged:,} rows from {filename}")

            versions = _versions_to_seed(cursor, seed_all, DEFAULT_VERSIONS_TO_KEEP)
            _reject_partial_seed_over_fuller_database(cursor, versions)
            _upsert_tes_versions(cursor, versions)
            with _timed("conditions"):
                _upsert_conditions(cursor, versions)
            with _timed("valuesets"):
                _upsert_valuesets(cursor, versions)
            with _timed("codes"):
                _upsert_codes(cursor, versions)
            with _timed("memberships"):
                _refresh_memberships(cursor, versions)

            for table in STAGE_TABLES:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

    logger.info(
        f"⏱️  Processed data loaded in {time.perf_counter() - start:.3f} seconds"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # bare load_dotenv walks up from the working directory, matching tes/fetch.
    # An absolute path here rotted silently when this module moved directories.
    load_dotenv()

    seed_all_env = os.getenv("SEED_ALL_TES_DATA")
    env = os.getenv("ENV")
    seed_all = seed_all_env == "true" if seed_all_env else env != "local"

    url = os.getenv("DB_URL")
    password = os.getenv("DB_PASSWORD")

    if not url or not password:
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
        raise SystemExit(1)

    load_processed_data(db_url=url, db_password=password, seed_all=seed_all)

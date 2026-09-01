import csv
from io import StringIO
from uuid import UUID

from packaging.version import parse
from psycopg.rows import class_row

from app.db.conditions.model import DbCondition
from app.db.configurations.db import (
    get_configurations_by_ids_db,
    insert_configuration_db,
)
from app.db.pool import AsyncDatabaseConnection
from app.db.tes.db import apply_latest_tes_to_existing_drafts_db
from app.db.tes.model import ConditionDiffExportData, DbTes, TesUpdate


def get_latest_tes_version(available_versions: list[DbTes]) -> DbTes:
    """
    Given a list of TES versions, finds and returns the latest.

    Args:
        available_versions (list[DbTes]): All available TES versions

    Returns:
        DbTes: The latest version
    """
    return max(available_versions, key=lambda av: parse(av.version))


def sort_tes_updates_by_version(updates: list[DbTes]) -> list[TesUpdate]:
    """
    Given a list of TES updates, sorts and returns the list by version.

    Args:
        updates (list[DbTes]): An unsorted list of available DB TES objects

    Returns:
        list[TesUpdate]: A sorted list of TES updates
    """
    tes_updates = [
        TesUpdate(id=t.id, version=t.version, created_at=t.created_at) for t in updates
    ]
    return sorted(tes_updates, key=lambda d: parse(d.version), reverse=True)


type Filename = str
type FileContents = str


def build_tes_export_csv(
    diff_data: ConditionDiffExportData, cur_version: str
) -> tuple[Filename, FileContents]:
    """
    Build the export CSV for a condition within a TES update given the relevant data.

    Args:
        diff_data (ConditionDiffExportData): Data derived from the DB with all codes added/removed for a condition
        cur_version (str): The current TES version to put in the filename

    Returns:
        tuple[Filename, FileContents]: CSV info in tuple form
    """
    return (
        _build_export_filename(diff_data.condition_name, version=cur_version),
        _build_csv_row_data(diff_data=diff_data),
    )


def _build_csv_row_data(diff_data: ConditionDiffExportData):
    with StringIO() as csv_text:
        writer = csv.writer(csv_text)
        writer.writerow(
            ["Condition Code Set", "Code", "Code System", "Display Name", "Change"]
        )

        removed = diff_data.removed_codes
        added = diff_data.added_codes

        for code in removed:
            writer.writerow(
                [
                    diff_data.condition_name,
                    code.code,
                    code.system_name,
                    code.display,
                    "Removed",
                ]
            )
        for code in added:
            writer.writerow(
                [
                    diff_data.condition_name,
                    code.code,
                    code.system_name,
                    code.display,
                    "Added",
                ]
            )

        return csv_text.getvalue()


def _build_export_filename(
    cond_grouper: str,
    version: str,
) -> str:
    """Build filename for condition TES diff export."""
    condition_grouper = cond_grouper.replace(" ", "-")
    return f"{condition_grouper}_TES_v{version}_change_summary.csv"


async def apply_updates_to_configurations(
    configuration_ids: list[str],
    db: AsyncDatabaseConnection,
    user_id: UUID,
    jurisdiction_id: str,
) -> tuple[int, int, list[str], list[str]]:
    """
    Apply TES updates to configurations.

    For draft configurations: Updates them with latest TES code sets.
    For active configurations: Creates new drafts with latest TES code sets.

    Returns: (drafts_updated, drafts_created, updated_ids, created_ids)
    """
    if not configuration_ids:
        return 0, 0, [], []

    # Convert string IDs to UUIDs
    uuid_ids = [UUID(cid) for cid in configuration_ids]

    # Fetch configurations to split into drafts and active
    configs = await get_configurations_by_ids_db(
        ids=uuid_ids, jurisdiction_id=jurisdiction_id, db=db
    )

    draft_ids = []
    active_ids = []

    for config in configs:
        if config.status == "draft":
            draft_ids.append(config.id)
        elif config.status == "active":
            active_ids.append(config.id)

    # 1. Update existing drafts
    updated_uuids = await apply_latest_tes_to_existing_drafts_db(
        db=db, configuration_ids=draft_ids, jurisdiction_id=jurisdiction_id
    )
    updated_ids = [str(uid) for uid in updated_uuids]

    # 2. Create new drafts from active configurations
    created_ids = []
    for active_id in active_ids:
        # Find the config object for the active_id
        active_config = next(c for c in configs if c.id == active_id)

        # Use insert_configuration_db to clone the active config into a new draft.
        # We need a condition object for insert_configuration_db.
        # We can use the primary condition of the active config.
        primary_condition_id = active_config.condition_id
        # We need the actual DbCondition object.
        # Since we don't have a direct get_condition_by_id_db in the imports,
        # we can use the fact that insert_configuration_db calls get_latest_tes_condition_db.
        # However, insert_configuration_db's first arg is 'condition'.
        # Let's look at insert_configuration_db again.
        # It calls: latest_condition = await get_latest_tes_condition_db(condition=condition, db=db)
        # If we pass the primary condition of the active config, it will find the latest TES version of it.

        # We need to fetch the DbCondition object for the primary condition.
        # I'll use a quick query or find a helper.
        # Actually, let's just use the primary condition's ID to get the object.
        # Since I can't easily add a new DB function, I'll use the existing ones.
        # Wait, I can just import get_condition_by_id_db if it exists, or use a simple query.
        # Let's check app.db.conditions.db.

        # For now, I will use a simple query to get the condition object.
        async with (
            db.get_connection() as conn,
            conn.cursor(row_factory=class_row(DbCondition)) as cur,
        ):  # Need to import DbCondition
            await cur.execute(
                "SELECT * FROM conditions WHERE id = %s", (primary_condition_id,)
            )
            condition_obj = await cur.fetchone()

        if not condition_obj:
            continue

        new_config = await insert_configuration_db(
            condition=condition_obj,
            user_id=user_id,
            jurisdiction_id=jurisdiction_id,
            db=db,
            config_to_clone=active_config,
        )

        if new_config:
            # Now apply the latest TES to this newly created draft
            await apply_latest_tes_to_existing_drafts_db(
                db=db,
                configuration_ids=[new_config.id],
                jurisdiction_id=jurisdiction_id,
            )
            created_ids.append(str(new_config.id))

    return len(updated_ids), len(created_ids), updated_ids, created_ids

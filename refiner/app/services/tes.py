import csv
from io import StringIO

from packaging.version import parse

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
    diff_data: ConditionDiffExportData, cur_tes_version: str
) -> tuple[Filename, FileContents]:
    """
    Build the export CSV for a condition within a TES update given the relevant data.

    Args:
        diff_data (ConditionDiffExportData): Data derived from the DB with all codes added/removed for a condition
        cur_tes_version (str): The current TES version to put in the filename

    Returns:
        tuple[Filename, FileContents]: CSV info in tuple form
    """
    return (
        _build_export_filename(diff_data.condition_name, version=cur_tes_version),
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
    condition_grouper = cond_grouper.replace(" ", "_")
    return f"{condition_grouper}_TES_v{version}_change_summary.csv"

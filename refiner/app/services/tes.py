from packaging.version import parse

from app.db.tes.model import DbTes
from app.api.v1.tes import TesUpdate


def get_latest_tes_version(available_versions: list[DbTes]) -> DbTes:
    """
    Given a list of TES versions, finds and returns the latest.

    Args:
        available_versions (list[DbTes]): All available TES versions

    Returns:
        DbTes: The latest version
    """
    return max(available_versions, key=lambda av: parse(av.version))


def sort_tes_diffs_by_version(updates: list[DbTes]) -> list[TesUpdate]:
    """
    Given a list of TES updates, sorts and returns the list by version.

    Args:
        available_diffs (list[TesUpdate]): An unsorted list of available TES Updates

    Returns:
        list[TesUpdate]: A sorted list of TES updates
    """
    tes_updates = [
        TesUpdate(id=t.id, version=t.version, created_at=t.created_at) for t in updates
    ]
    return sorted(tes_updates, key=lambda d: parse(d.version))

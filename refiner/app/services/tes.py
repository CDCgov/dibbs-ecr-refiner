from packaging.version import parse

from app.db.tes.model import DbTes, TesUpdate


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

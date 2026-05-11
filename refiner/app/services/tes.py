from packaging.version import parse


def get_latest_tes_version(available_versions: list[str]) -> str:
    """
    Given a list of TES versions, finds and returns the latest.

    Args:
        available_versions (list[str]): All available TES versions

    Returns:
        str: The latest version
    """
    return max(available_versions, key=lambda v: parse(v))

from app.db.configurations.model import DbConfiguration


def get_canonical_url_to_highest_inactive_version_map(
    configs: list[DbConfiguration],
) -> dict[str, DbConfiguration]:
    """
    Creates a dictionary that maps a condition URL to the highest inactive version configuration.

    Args:
        configs (list[DbConfiguration]): List of DbConfigurations

    Returns:
    a dictionary with the structure:
        key = Condition canonical URL
        value = Inactive configuration with highest version number
    """
    highest_version_inactive_configs_map: dict[str, DbConfiguration] = {}
    for c in configs:
        if c.status == "inactive":
            key = c.condition_canonical_url
            if (
                key not in highest_version_inactive_configs_map
                or c.version > highest_version_inactive_configs_map[key].version
            ):
                highest_version_inactive_configs_map[key] = c
    return highest_version_inactive_configs_map

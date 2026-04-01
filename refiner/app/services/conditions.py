import re
import unicodedata

from app.db.conditions.db import get_conditions_by_ids
from app.db.conditions.model import (
    ConditionMappingPayload,
    ConditionMapValue,
    DbCondition,
)
from app.db.configurations.db import get_configurations_db
from app.db.pool import AsyncDatabaseConnection


async def get_conditions_with_active_config(
    jurisdiction_id: str, db: AsyncDatabaseConnection
) -> list[DbCondition]:
    """
    Given a jurisdiction ID, returns a list of conditions that have an active configuration.

    Args:
        jurisdiction_id (str): The jurisdiction ID
        db (AsyncDatabaseConnection): The database connection

    Returns:
        list[DbCondition]: List of DbCondition with an active configuration within the JD.
    """

    # Get all active configurations
    active_configs_in_jd = await get_configurations_db(
        jurisdiction_id=jurisdiction_id, status="active", db=db
    )

    # Get the conditions from the active configs
    active_config_ids = [active.condition_id for active in active_configs_in_jd]
    return await get_conditions_by_ids(ids=active_config_ids, db=db)


def get_computed_condition_name(condition_name: str) -> str:
    """
    Given a condition name returns the computed name.

    For example:
    - `COVID-19` becomes `COVID19`
    - `Drowning and Submersion` becomes `DrowningandSubmersion`

    Args:
        condition_name (str): The name of the condition

    Returns:
        str: The computed condition name
    """
    # !!NOTE!!
    # TES versions 1-3 have the computed name `Tickborne_relapsing_feverTBRF` and
    # version 4 has the computed name `Tickborne_relapsing_fever_TBRF` which is probably a bug

    normalized = unicodedata.normalize("NFKD", condition_name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"\s+", "", normalized.strip())
    normalized = re.sub(r"[^A-Za-z0-9_]", "", normalized)
    return normalized


def create_condition_mapping_payload(
    conditions: list[DbCondition],
) -> ConditionMappingPayload:
    """
    Maps RSG codes to all possible matching CGs.

    Args:
        conditions (list[DbCondition]): A list of condition information

    Returns:
        ConditionMappingPayload: Typed dictionary containing condition mapping info
    """
    payload = ConditionMappingPayload()
    for condition in conditions:
        name = condition.display_name
        tes_version = condition.version

        for rsg in condition.child_rsg_snomed_codes:
            if not rsg or not rsg.strip():
                continue

            rsg = rsg.strip()
            value = ConditionMapValue(
                canonical_url=condition.canonical_url,
                name=get_computed_condition_name(name),
                tes_version=tes_version,
            )

            exists = payload.mappings.get(rsg)
            if exists is not None and exists != value:
                raise ValueError(
                    f"Collision for RSG code {rsg}: "
                    f"{exists.canonical_url} vs {condition.canonical_url}"
                )

            payload.mappings[rsg] = value

    return payload

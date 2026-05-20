from app.db.conditions.model import (
    ConditionMappingPayload,
    ConditionMapValue,
    DbCondition,
)
from app.services.conditions.naming import get_computed_condition_name


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

from typing import TypedDict
from urllib.parse import urlparse
from uuid import UUID

from app.db.conditions.model import DbCondition


def extract_uuid_from_canonical_url(url: str) -> UUID:
    """
    Given a `canonical_url`, extracts and returns the UUID at the end of it.

    For example, given `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/c435a017-41e6-4030-b6d1-0bda2eb05b1f`
    the function returns `c435a017-41e6-4030-b6d1-0bda2eb05b1f`

    Args:
        url (str): The canonical URL

    Returns:
        UUID: The UUID at the end of the canonical URL
    """
    parsed = urlparse(url)
    last_segment = parsed.path.rstrip("/").split("/")[-1]
    return UUID(last_segment)


class ConditionMapValue(TypedDict):
    """
    Condition data mapped to an RSG.
    """

    condition_grouper_id: str
    name: str


type ConditionMappingPayload = dict[str, ConditionMapValue]


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
    mapping: ConditionMappingPayload = {}
    for condition in conditions:
        cg_uuid = extract_uuid_from_canonical_url(condition.canonical_url)
        name = condition.display_name

        for rsg in condition.child_rsg_snomed_codes:
            exists = mapping.get(rsg)
            value: ConditionMapValue = {
                "condition_grouper_id": str(cg_uuid),
                "name": name,
            }

            if exists is not None and exists != value:
                raise ValueError(
                    f"Collision for RSG code {rsg}: "
                    f"{exists['condition_grouper_id']} vs {cg_uuid}"
                )

            mapping[rsg] = value

    return mapping

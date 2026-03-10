import re
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


# TODO: Collect this from the TES data directly instead?
def _get_computed_name(text: str) -> str:
    normalized = re.sub(r"\s+", "_", text.strip())
    normalized = re.sub(r"[^A-Za-z0-9_]", "", normalized)

    # !!NOTE!!
    # TES versions 1-3 have the computed name `Tickborne_relapsing_feverTBRF` and
    # version 4 has the computed name `Tickborne_relapsing_fever_TBRF` which is probably a bug
    overrides = {
        "NonStreptococcal_Toxic_Shock_Syndrome": "NonStreptococcal_ToxicShock_Syndrome",
        "Tickborne_relapsing_fever_TBRF": "Tickborne_relapsing_feverTBRF",
    }

    return overrides.get(normalized, normalized)


class ConditionMapValue(TypedDict):
    """
    Condition data mapped to an RSG.
    """

    condition_grouper_id: str
    name: str
    tes_version: str


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
        tes_version = condition.version

        for rsg in condition.child_rsg_snomed_codes:
            exists = mapping.get(rsg)
            value: ConditionMapValue = {
                "condition_grouper_id": str(cg_uuid),
                "name": _get_computed_name(name),
                "tes_version": tes_version,
            }

            if exists is not None and exists != value:
                raise ValueError(
                    f"Collision for RSG code {rsg}: "
                    f"{exists['condition_grouper_id']} vs {cg_uuid}"
                )

            mapping[rsg] = value

    return mapping

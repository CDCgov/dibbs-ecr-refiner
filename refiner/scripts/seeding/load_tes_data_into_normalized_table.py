from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID, uuid4

from lib import (
    ConditionData,
    FhirCodeTuple,
    VsCanonicalUrl,
    VsVersion,
    load_valuesets_from_all_files,
)

from scripts.seeding.load_tes_data import _build_condition_groupers

type UrlVersionTuple = tuple[VsCanonicalUrl, VsVersion]
type ConditionId = UUID
type CodeId = UUID


# TODO: to be fleshed out in the actual script
@dataclass
class _IdentifiableCode:
    code_id: CodeId
    code_data: FhirCodeTuple


# TODO: to be fleshed out in the actual script
@dataclass
class _IdentifiableCondition:
    condition_id: ConditionId
    condition_data: ConditionData


def upsert_conditions(conditions: list[_IdentifiableCondition]):
    """
    Stub for upsert of conditions.
    """
    # do the relevant SQL work
    return True


def upsert_codes(codes: list[_IdentifiableCode]):
    """
    Stub for upsert of conditions.
    """

    # do the relevant SQL work, using the UUID from _Code to insert things into the DB
    return True


def upsert_condition_to_codes_relationship(
    condition_to_code_relationships: dict[ConditionId, list[CodeId]],
):
    """
    Stub for upsert of condition to codes relationship.
    """

    # do the relevant SQL work, using the UUIDs from _ConditionData
    # to insert store the condition and code entity relationships
    return True


# build conditions to insert
def _build_processed_conditions() -> dict[UrlVersionTuple, _IdentifiableCondition]:

    conditions_map: dict[UrlVersionTuple, _IdentifiableCondition] = defaultdict()

    # parse out the valuesets from the TES files like we were doing previously
    all_valuesets_map = load_valuesets_from_all_files()
    condition_groupers = _build_condition_groupers(valuesets_map=all_valuesets_map)

    for parent in condition_groupers:
        # have the application generate the UUID to make relationships easier to maintain
        condition_id = uuid4()
        data = ConditionData(parent, all_valuesets_map)
        url = parent.get("url")
        version = parent.get("version")

        if not isinstance(url, str) or not isinstance(version, str):
            raise Exception("url or version is None")

        url_version_key: UrlVersionTuple = (url, version)

        condition_to_insert = _IdentifiableCondition(
            condition_id=condition_id,
            condition_data=data,
        )

        # note the inserted condition ID in the relationship map
        conditions_map[url_version_key] = condition_to_insert

    return conditions_map


def _build_processed_codes(
    condition_to_codes_map: dict[UrlVersionTuple, _IdentifiableCondition],
) -> tuple[list[_IdentifiableCode], dict[ConditionId, list[CodeId]]]:
    codes_to_insert: list[_IdentifiableCode] = []
    condition_to_code_relationships: dict[ConditionId, list[CodeId]] = defaultdict(list)

    for c in condition_to_codes_map.values():
        cur_condition_codes = c.condition_data.all_codes
        identified_codes = [
            # generate the UUID in code
            _IdentifiableCode(code_id=uuid4(), code_data=code)
            for code in cur_condition_codes
        ]
        codes_to_insert.extend(identified_codes)

        # use generated UUID to mark condition <> code relationship for future processing
        condition_to_code_relationships[c.condition_id] = [
            code.code_id for code in identified_codes
        ]

    return (codes_to_insert, condition_to_code_relationships)


# munge and upsert conditions
condition_to_codes_map = _build_processed_conditions()

upsert_conditions(conditions=list(condition_to_codes_map.values()))

codes_to_insert, condition_to_code_relationships = _build_processed_codes(
    condition_to_codes_map=condition_to_codes_map
)
# and codes
upsert_codes(codes=codes_to_insert)

# and finally their relationships
upsert_condition_to_codes_relationship(
    condition_to_code_relationships=condition_to_code_relationships
)

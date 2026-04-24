from collections import defaultdict
from dataclasses import asdict, dataclass
from uuid import UUID, uuid4

from lib import (
    VsCanonicalUrl,
    VsDict,
    VsVersion,
    get_child_rsg_valuesets,
    get_sibling_context_valuesets,
    load_valuesets_from_all_files,
)

# parse data from TES groupers like we are currently
type UrlVersionTuple = tuple[VsCanonicalUrl, VsVersion]
type CodeId = str


# TODO: to be fleshed out in the actual script
@dataclass
class _Code:
    code_id: UUID
    code_data: VsDict


@dataclass
class _ConditionData:
    condition_id: UUID
    condition_data: VsDict


class ConditionCodeList:
    """Class that represents a condition's relationship to a list of relevant codes."""

    condition: _ConditionData
    child_rsg_codes: list[_Code]
    valueset_codes: list[_Code]

    def __init__(
        self,
        condition: _ConditionData,
        child_rsg_codes: list[_Code],
        valueset_codes: list[_Code],
    ):
        """
        Initalizes a condition based on the ID with empty code arrays.
        """
        self.condition = condition
        self.child_rsg_codes = child_rsg_codes
        self.valueset_codes = valueset_codes

    def add_child_rsg_codes(self, code_list: list[_Code]):
        """
        Extend child_rsg list with code.
        """
        self.child_rsg_codes.extend(code_list)

    def add_valueset_codes(self, code_list: list[_Code]):
        """
        Extend valueset with code.
        """
        self.valueset_codes.extend(code_list)

    def get_deduped_codes(self) -> list[_Code]:
        """
        Get list of deduped codes for insert.
        """
        code_set = set(self.child_rsg_codes + self.valueset_codes)
        return list(code_set)


def upsert_conditions(conditions: list[_ConditionData]):
    """
    Stub for upsert of conditions.
    """
    # do the relevant SQL work
    return True


def upsert_codes(codes: list[list[_Code]]):
    """
    Stub for upsert of conditions.
    """

    # do the relevant SQL work
    return True


def upsert_code_to_condition_relationships(
    conditions: dict[UrlVersionTuple, ConditionCodeList],
):
    """
    Stub for upsert of conditions.
    """

    # do the relevant SQL work
    return True


# build conditions to insert
def _build_processed_conditions(
    vs_map: dict[UrlVersionTuple, VsDict],
    condition_to_codes_map: dict[UrlVersionTuple, ConditionCodeList],
) -> dict[UrlVersionTuple, _ConditionData]:
    processed_codes: dict[UrlVersionTuple, _ConditionData] = defaultdict()

    for url_version_key, condition_data in vs_map.items():
        # have the application generate the UUID to make relationships easier to maintain
        cur_condition_id = uuid4()

        # prepare data from the TES needed for insert
        condition_to_insert = _ConditionData(
            condition_id=cur_condition_id,
            condition_data=condition_data,
        )

        # note the inserted condition ID in the relationship map
        condition_to_codes_map[url_version_key] = ConditionCodeList(
            condition=condition_to_insert, child_rsg_codes=[], valueset_codes=[]
        )

    return processed_codes


# build codes to insert
def _build_processed_codes(
    vs_map: dict[UrlVersionTuple, VsDict],
    condition_to_codes_map: dict[UrlVersionTuple, ConditionCodeList],
) -> dict[UrlVersionTuple, list[_Code]]:
    processed_codes: dict[UrlVersionTuple, list[_Code]] = defaultdict(list)

    for url_version_key in vs_map.keys():
        condition_to_code_trace = condition_to_codes_map[url_version_key]
        related_condition = condition_to_code_trace.condition

        # the "get valuesets" functions will need to be modified,
        # but hopefully illustrative of what we'll need to do
        child_rsgs = get_child_rsg_valuesets(
            parent=asdict(related_condition),
            all_vs_map=all_valuesets_map,
        )

        # add related codes into trace
        condition_to_code_trace.add_child_rsg_codes(
            # have the application generate the UUID to make relationships easier to maintain
            [_Code(code_id=uuid4(), code_data=c) for c in child_rsgs]
        )

        sibling_codes = get_sibling_context_valuesets(
            parent=related_condition.condition_data, all_vs_map=all_valuesets_map
        )
        condition_to_code_trace.add_valueset_codes(
            # have the application generate the UUID to make relationships easier to maintain
            [_Code(code_id=uuid4(), code_data=c) for c in sibling_codes]
        )

    return processed_codes


condition_to_codes_map: dict[UrlVersionTuple, ConditionCodeList] = defaultdict()

# parse out the valuesets from the TES files like we were doing previously
all_valuesets_map = load_valuesets_from_all_files()

# munge and upsert conditions
processed_conditions = _build_processed_conditions(
    vs_map=all_valuesets_map, condition_to_codes_map=condition_to_codes_map
)
upsert_conditions(conditions=list(processed_conditions.values()))

# munge and upsert codes
processed_codes = _build_processed_codes(
    vs_map=all_valuesets_map, condition_to_codes_map=condition_to_codes_map
)
upsert_codes(codes=list(processed_codes.values()))

# parse condition <> codes relationship and upsert the result into table
upsert_code_to_condition_relationships(condition_to_codes_map)

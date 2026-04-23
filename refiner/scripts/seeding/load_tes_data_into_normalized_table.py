from collections import defaultdict
from dataclasses import asdict, dataclass
from uuid import UUID, uuid4

from lib import (
    ConditionData,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
    get_child_rsg_valuesets,
    load_valuesets_from_all_files,
)

# parse data from TES groupers like we are currently
type UrlVersionTuple = tuple[VsCanonicalUrl, VsVersion]
type CodeId = str


# TODO: to be fleshed out in the actual script
@dataclass
class _ConditionData:
    condition_id: UUID
    condition_data: VsDict


@dataclass
class _Code:
    code_id: UUID
    code_data: VsDict


class ConditionCodeList:
    """Class that represents a condition's relationship to a list of relevant codes."""

    condition: _ConditionData
    child_rsg_codes: list[dict]
    valueset_codes: list[dict]

    def __init__(self, condition: _ConditionData):
        """
        Initalizes a condition based on the ID with empty code arrays.
        """
        self.condition = condition
        self.child_rsg_codes = []
        self.tes_valueset_ids = []

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


condition_to_codes_map: dict[UrlVersionTuple, ConditionCodeList] = defaultdict()


# build conditions to insert
def _build_processed_conditions(
    vs_map: dict[UrlVersionTuple, VsDict],
) -> dict[UrlVersionTuple, list[ConditionData]]:
    processed_codes: dict[UrlVersionTuple, list[ConditionData]] = defaultdict(list)

    for url_version_key, condition_data in vs_map.items():
        # have the application generate the UUID to make relationships easier to maintain
        cur_condition_id = uuid4()

        # prepare data from the TES needed for insert
        condition_to_insert = _ConditionData(
            condition_id=cur_condition_id, condition_data=condition_data
        )

        # note the inserted condition ID in the relationship map
        condition_to_codes_map[url_version_key] = ConditionCodeList(condition_to_insert)

    return processed_codes


# build codes to insert
def _build_processed_codes(
    vs_map: dict[UrlVersionTuple, VsDict],
) -> dict[UrlVersionTuple, list[VsDict]]:
    processed_codes: dict[UrlVersionTuple, list[VsDict]] = defaultdict(list)

    for url_version_key, code_data in vs_map.items():
        # have the application generate the UUID to make relationships easier to maintain
        cur_code_uuid = uuid4()

        relationship_to_extend = condition_to_codes_map[url_version_key]
        child_rsgs = get_child_rsg_valuesets(
            parent=asdict(relationship_to_extend.condition),
            all_vs_map=all_valuesets_map,
        )
        relationship_to_extend.add_child_rsg_codes(
            [_Code(code_id=cur_code_uuid, code_data=c) for c in child_rsgs]
        )

    return processed_codes


all_valuesets_map = load_valuesets_from_all_files()
processed_conditions = _build_processed_conditions(vs_map=all_valuesets_map)
# await upsert_conditions(processed_codes.items())

processed_codes = _build_processed_codes(all_valuesets_map)
# await upsert_codes(processed_codes.items())

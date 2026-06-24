from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.db.codes.model import CodedConcept
from app.services.ecr.specification.constants import OID_TO_SYSTEM_KEY_MAP

from ..db.conditions.model import DbCondition, DbConditionCoding
from ..db.configurations.model import DbNarrativeAction

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Processed` class (e.g., ProcessedConfiguration) holds the final, ready-to-use data.
# 2. The `Processed` class has a `.from_dict()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================
type CodeSystemKey = str
type Oid = str


def index_condition_code_list_by_system(
    condition: DbCondition, system_keys_to_index_by: list[CodeSystemKey]
) -> dict[CodeSystemKey, list[DbConditionCoding]]:
    """
    Utility method to index condition code lists as stored into the DB by the ID values. Useful for various processing jobs processing.
    """
    result: dict[CodeSystemKey, list[DbConditionCoding]] = defaultdict(list)
    for s in system_keys_to_index_by:
        # TODO: replace this string mapping with proper read to the codes table
        condition_column_index = f"{s}_codes"
        result[s] = getattr(condition, condition_column_index, [])

    return result


@dataclass(frozen=True)
class Coding(CodedConcept):
    """
    A code + display + system triple, representing a single coded concept.

    This is the fundamental unit of terminology data throughout the refinement
    pipeline. It carries enough context for both matching (code + system) and
    enrichment (display). For `system` the value will be an OID when known,
    and a human label for custom codes with "Other".
    """

    system_oid: str = ""


type Code = str


@dataclass(frozen=True)
class CodeSystemSets:
    """
    Codes organized by code system for efficient, unambiguous lookup.

    Each dict is keyed by code string → Coding object, giving O(1) lookup
    and access to the display name when a match is found.

    This replaces the flat set[str] approach, enabling:
    - Per-section code system constraints (only check SNOMED in Problems, etc.)
    - displayName enrichment at match time (the Coding carries the display)
    - Backward compatibility via the all_codes property
    """

    oid_to_system_map: dict[Oid, CodeSystemKey] = field(default_factory=dict)
    system_to_code_maps: dict[CodeSystemKey, dict[Code, Coding]] = field(
        default_factory=dict
    )

    @property
    def all_codes(self) -> set[str]:
        """
        Flat set of all code strings across all systems.

        Use this for sections that don't have entry_match_rules
        defined yet (the old generic search path).
        """

        return {
            code for system_dict in self._iter_dicts() for code in system_dict.keys()
        }

    def _iter_dicts(self) -> Iterator[dict[str, Coding]]:
        """Helper to iterate over all dictionary fields in the dataclass."""
        for f in self.system_to_code_maps.values():
            if isinstance(f, dict):
                yield f

    def _get_system_dict(
        self,
        code_system_oid: str,
    ) -> dict[str, Coding] | None:
        """
        Resolve an OID to the corresponding code system dict.

        Args:
            code_system_oid: The code system OID to resolve.

        Returns:
            The dict for that system, or None if the OID is unknown.
        """
        matching_system = self.oid_to_system_map.get(code_system_oid)
        if (
            matching_system is None
            or matching_system not in self.system_to_code_maps.keys()
        ):
            return None
        return self.system_to_code_maps[matching_system]

    def find_match(
        self, code: str, code_system_oid: str | None = None
    ) -> Coding | None:
        """
        Look up a code, optionally constrained to a specific code system.

        When code_system_oid is provided, only that system's codes are checked.
        When None, all systems are checked (fallback for sections without
        code system constraints).

        Args:
            code: The code string to look up.
            code_system_oid: Optional OID to constrain the search.

        Returns:
            The matching Coding if found, or None.
        """

        if code_system_oid is not None:
            target = self._get_system_dict(code_system_oid)
            # unknown OID — fall through to check all systems
            # this handles local/proprietary code systems gracefully
            if target is not None:
                return target.get(code)

        # check all systems (either no OID given, or OID was unknown)
        for system_dict in self._iter_dicts():
            if code in system_dict:
                return system_dict[code]
        return None

    def has_match(self, code: str, code_system_oid: str | None = None) -> bool:
        """
        Check if a code matches without returning the full Coding.

        Convenience method for cases where you only need a boolean.
        """

        return self.find_match(code, code_system_oid) is not None

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        """
        Serialize CodeSystemSets to a dictionary for S3 storage.

        Each system is serialized as a list of Coding dicts. This format
        is written to active.json during activation and deserialized by
        from_dict when lambda reads the configuration.

        Returns:
            dict: A dictionary with system names as keys and lists of
                  Coding dicts as values.
        """

        def _serialize_system(
            system_dict: dict[str, Coding],
        ) -> list[dict[str, str]]:
            return [
                {
                    "code": coding.code,
                    "display": coding.display,
                    "system": coding.system_oid,
                }
                for coding in system_dict.values()
            ]

        return {
            system_key: _serialize_system(system_map)
            for system_key, system_map in self.system_to_code_maps.items()
        }

    @classmethod
    def from_dict(
        cls,
        coding_by_code_system: dict[CodeSystemKey, list[dict[Code, str]]],
        oid_to_system_map: dict[Oid, CodeSystemKey],
    ) -> "CodeSystemSets":
        """
        Deserialize a CodeSystemSets from a dictionary (read from S3).

        This is the inverse of to_dict. Each system key maps to a list
        of Coding dicts which are reconstructed into the per-system
        lookup dictionaries.

        Args:
            coding_by_code_system: Dictionary with system names as keys and lists of Coding dicts as values, as stored in S3.
            oid_to_system_map: Map between OID and internal system key used to index S3 code system information

        Returns:
            CodeSystemSets: A fully populated CodeSystemSets with codes
                           routed to the correct system dictionaries.
        """

        def _deserialize_system(
            codings: list[dict[str, str]] | None,
        ) -> dict[str, Coding]:
            if codings is None:
                return {}
            return {
                item["code"]: Coding(
                    code=item["code"],
                    display=item.get("display", ""),
                    system_oid=item.get("system", ""),
                )
                for item in codings
            }

        system_to_code_maps = {
            system_key: _deserialize_system(coding_by_code_system.get(system_key))
            if coding_by_code_system.get(system_key)
            else {}
            for system_key in oid_to_system_map.values()
        }

        return cls(
            system_to_code_maps=system_to_code_maps,
            oid_to_system_map=oid_to_system_map,
        )


# NOTE:
# CONFIGURATION PROCESSING
# =============================================================================


class Section(BaseModel):
    """
    Section data coming from an active.json S3 file.
    """

    code: str
    name: str
    action: str
    narrative: DbNarrativeAction
    include: bool


class ProcessedConfigurationData(BaseModel):
    """
    ProcessedConfiguration data coming from an active.json S3 file.

    active.json stores code data in code_system_sets. The runtime flat codes set
    is derived from code_system_sets when building the ProcessedConfiguration.
    """

    sections: list[Section]
    included_condition_rsg_codes: set[str]
    code_system_sets: dict[str, list[dict[str, str]]]


@dataclass(frozen=True)
class ProcessedConfiguration:
    """
    Represents the processed set of codes from a configuration, ready for refinement.

    This model supports both flat-code matching and code-system-aware matching:

       - codes: Flat set of all code strings, derived from code_system_sets at read time
         and used for fallback matching when no specific entry matching rules are in place.
       - code_system_sets: Structured per-system lookup used by the section-aware matching path.


    Both fields are populated from the same source data. When the IG does not prescribe strict **SHALL**
    entry matching rules then we can fall back to using `codes`, whereas sections that have strict **SHALL**
    entry matching rules they can use `code_system_sets`.
    """

    codes: set[str]
    code_system_sets: CodeSystemSets
    section_processing: list[dict]
    included_condition_rsg_codes: set[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessedConfiguration":
        """
        Creates a ProcessedConfiguration from a validated dictionary.

        code_system_sets is required in active.json. The runtime flat codes set
        is derived from all coding objects across all code systems.

        Args:
            data (dict): Input dictionary with required data.

        Returns:
            ProcessedConfiguration: A ProcessedConfiguration built from the dictionary.
        """

        validated = ProcessedConfigurationData.model_validate(data)

        code_system_sets = CodeSystemSets.from_dict(
            coding_by_code_system=validated.code_system_sets,
            oid_to_system_map=OID_TO_SYSTEM_KEY_MAP,
        )

        codes = {
            coding["code"]
            for coding_list in validated.code_system_sets.values()
            for coding in coding_list
        }

        return cls(
            codes=codes,
            code_system_sets=code_system_sets,
            section_processing=[s.model_dump() for s in validated.sections],
            included_condition_rsg_codes=validated.included_condition_rsg_codes,
        )

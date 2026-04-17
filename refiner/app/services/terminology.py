from collections import defaultdict
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field, fields
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..db.conditions.model import DbCondition, DbConditionCoding

if TYPE_CHECKING:
    from ..db.configurations.model import DbConfiguration

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Payload` class (e.g., ConfigurationPayload) holds raw DB models.
# 2. A `Processed` class (e.g., ProcessedConfiguration) holds the final, ready-to-use data.
# 3. The `Processed` class has a `.from_payload()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================


# CODE SYSTEM MODELS
# =============================================================================
class CodeSystem(StrEnum):
    """
    An Enum for code systems.
    """

    # !IMPORTANT!
    # If you add something here, be sure to also update the value in the corresponding
    # values in the CodeSystemSets class and in the database references in DBCondition
    # and related classes. It's probably worth it at some point for us to centralize
    # code system information into a source of truth in the db.
    LOINC = "LOINC"
    SNOMED = "SNOMED"
    ICD10 = "ICD-10"
    RXNORM = "RxNorm"
    CVX = "CVX"
    OTHER = "Other"

    @classmethod
    def sanitize(cls, value: str) -> "CodeSystem":
        """
        Convert value to a santized name from the CodeSystem.
        """
        if not isinstance(value, str):
            raise ValueError(f"System name provided: {value} is invalid.")

        mapping = {item.value.lower(): item for item in cls}
        sanitized = mapping.get(value.strip().lower())
        if not sanitized:
            raise ValueError(f"System name provided: {value} is invalid.")

        return sanitized

    @property
    def oid(self) -> str:
        """
        Get the corresponding code system OID.
        """

        return SYSTEM_LABEL_TO_OID[self]

    def format_system_string(self) -> str:
        """
        Utility property to format system name into a value that can index dictionaries, with special formatting for ICD-10 to remove the hyphen.
        """

        if self.value == "ICD-10":
            return "icd10"

        return self.value.lower()

    @classmethod
    def _missing_(cls, value: object):
        if not isinstance(value, str):
            return None
        normalized_value = value.lower()
        mapping = {
            "loinc": cls.LOINC,
            "snomed": cls.SNOMED,
            "icd10": cls.ICD10,
            "icd-10": cls.ICD10,
            "cvx": cls.CVX,
            "rxnorm": cls.RXNORM,
            "other": cls.OTHER,
        }

        return mapping.get(normalized_value)


def index_condition_code_list_by_system(
    condition: DbCondition,
) -> dict[CodeSystem, list[DbConditionCoding]]:
    """
    Utility method to index condition code lists as stored into the DB by the system enum values. Useful for various processing jobs processing.
    """

    result: dict[CodeSystem, list[DbConditionCoding]] = defaultdict(list)
    for s in CodeSystem:
        condition_column_index = f"{s.format_system_string()}_codes"
        result[s] = getattr(condition, condition_column_index, [])

    return result


ALLOWED_CUSTOM_CODE_SYSTEMS: set[CodeSystem] = set(CodeSystem)
ALLOWED_CUSTOM_CODE_SYSTEM_NAMES = ", ".join(
    item.value for item in ALLOWED_CUSTOM_CODE_SYSTEMS
)

SYSTEM_LABEL_TO_OID: dict[CodeSystem, str] = {
    CodeSystem.SNOMED: "2.16.840.1.113883.6.96",
    CodeSystem.LOINC: "2.16.840.1.113883.6.1",
    CodeSystem.ICD10: "2.16.840.1.113883.6.90",
    CodeSystem.RXNORM: "2.16.840.1.113883.6.88",
    CodeSystem.CVX: "2.16.840.1.113883.12.292",
    CodeSystem.OTHER: "Other",  # fall back to generic string in the event of custom code system,
}

OID_TO_SYSTEM_LABEL = {
    oid: code_system.format_system_string()
    for code_system, oid in SYSTEM_LABEL_TO_OID.items()
}


@dataclass(frozen=True)
class Coding:
    """
    A code + display + system triple, representing a single coded concept.

    This is the fundamental unit of terminology data throughout the refinement
    pipeline. It carries enough context for both matching (code + system) and
    enrichment (display). For `system` the value will be an OID when known,
    and a human label for custom codes with "Other".
    """

    code: str
    display: str = ""
    system: str = ""


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

    snomed: dict[str, Coding] = field(default_factory=dict)
    loinc: dict[str, Coding] = field(default_factory=dict)
    icd10: dict[str, Coding] = field(default_factory=dict)
    rxnorm: dict[str, Coding] = field(default_factory=dict)
    cvx: dict[str, Coding] = field(default_factory=dict)
    other: dict[str, Coding] = field(default_factory=dict)

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
        for f in fields(self):
            val = getattr(self, f.name)
            if isinstance(val, dict):
                yield val

    def _get_system_dict(self, code_system_oid: str) -> dict[str, Coding] | None:
        """
        Resolve an OID to the corresponding code system dict.

        Args:
            code_system_oid: The code system OID to resolve.

        Returns:
            The dict for that system, or None if the OID is unknown.
        """

        attr_name = OID_TO_SYSTEM_LABEL.get(code_system_oid)
        if attr_name is None:
            return None
        return getattr(self, attr_name)

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

        def _serialize_system(system_dict: dict[str, Coding]) -> list[dict[str, str]]:
            return [
                {
                    "code": coding.code,
                    "display": coding.display,
                    "system": coding.system,
                }
                for coding in system_dict.values()
            ]

        return {
            "snomed": _serialize_system(self.snomed),
            "loinc": _serialize_system(self.loinc),
            "icd10": _serialize_system(self.icd10),
            "rxnorm": _serialize_system(self.rxnorm),
            "cvx": _serialize_system(self.cvx),
            "other": _serialize_system(self.other),
        }

    @classmethod
    def from_dict(cls, data: dict[str, list[dict[str, str]]]) -> "CodeSystemSets":
        """
        Deserialize a CodeSystemSets from a dictionary (read from S3).

        This is the inverse of to_dict. Each system key maps to a list
        of Coding dicts which are reconstructed into the per-system
        lookup dictionaries.

        Args:
            data: Dictionary with system names as keys and lists of
                  Coding dicts as values.

        Returns:
            CodeSystemSets: A fully populated CodeSystemSets with codes
                           routed to the correct system dictionaries.
        """

        def _deserialize_system(codings: list[dict[str, str]]) -> dict[str, Coding]:
            return {
                item["code"]: Coding(
                    code=item["code"],
                    display=item.get("display", ""),
                    system=item.get("system", ""),
                )
                for item in codings
            }

        return cls(
            snomed=_deserialize_system(data.get("snomed", [])),
            loinc=_deserialize_system(data.get("loinc", [])),
            icd10=_deserialize_system(data.get("icd10", [])),
            rxnorm=_deserialize_system(data.get("rxnorm", [])),
            cvx=_deserialize_system(data.get("cvx", [])),
            other=_deserialize_system(data.get("other", [])),
        )


# NOTE:
# CONFIGURATION PROCESSING
# =============================================================================


@dataclass(frozen=True)
class ConfigurationPayload:
    """
    Model representing the raw configuration data needed for refinement.

    This model is intentionally minimal to support both inline testing (from configuration building)
    and independent testing (from demo.py processing) patterns. The model focuses on just the
    essential data needed for refinement:

    - conditions: A list of all DbCondition objects to be considered.
    - configuration: The specific DbConfiguration object, which may contain custom codes.

    Note on Testing Patterns:
    - Independent testing: Uses RC SNOMED codes from the RR's coded information organizer to find
      the matching configuration. The RC SNOMED code comes from the RR, not the configuration itself.
    - Inline testing: Directly uses a configuration to test against input data, focusing only on
      the codes defined in that configuration.
    """

    configuration: "DbConfiguration"
    conditions: list[DbCondition]


class Section(BaseModel):
    """
    Section data coming from an active.json S3 file.
    """

    code: str
    name: str
    action: str
    narrative: bool
    include: bool


class ProcessedConfigurationData(BaseModel):
    """
    ProcessedConfiguration data coming from an active.json S3 file.

    Supports both the legacy format (flat codes only) and the enriched
    format (with code_system_sets). The enriched format is written by
    newer activation code.
    """

    codes: set[str] = Field(min_length=1)
    sections: list[Section]
    included_condition_rsg_codes: set[str]
    code_system_sets: dict[str, list[dict[str, str]]] | None = None


@dataclass(frozen=True)
class ProcessedConfiguration:
    """
    Represents the processed set of codes from a configuration, ready for refinement.

    This model supports both the existing flat-code matching path and the new
    code-system-aware matching path:

    - codes: Flat set of all code strings (used when no specific entry matching rules are in place)
    - code_system_sets: Structured per-system lookup (fed to new section-aware path)

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

        Supports both the enriched format (with code_system_sets) and the
        simple code search (flat codes only). When code_system_sets is present
        in the data, codes are routed to the correct per-system dictionaries
        with display names, enabling section-aware matching and displayName
        enrichment. When absent, all codes are placed in the 'other' bucket
        as a fallback.

        Args:
            data (dict): Input dictionary with required data.

        Returns:
            ProcessedConfiguration: A ProcessedConfiguration built from the dictionary.
        """

        validated = ProcessedConfigurationData.model_validate(data)

        if validated.code_system_sets is not None:
            # enriched format: deserialize the per-system code structure
            code_system_sets = CodeSystemSets.from_dict(validated.code_system_sets)
        else:
            # no system info available, put everything in 'other'
            other_codings = {code: Coding(code=code) for code in validated.codes}
            code_system_sets = CodeSystemSets(other=other_codings)

        return cls(
            codes=validated.codes,
            code_system_sets=code_system_sets,
            section_processing=[s.model_dump() for s in validated.sections],
            included_condition_rsg_codes=validated.included_condition_rsg_codes,
        )

    @classmethod
    def from_payload(cls, payload: ConfigurationPayload) -> "ProcessedConfiguration":
        """
        Create ProcessedConfiguration from a ConfigurationPayload object.

        This method aggregates codes from both the configuration's associated conditions and
        any custom codes defined on the configuration itself. Codes are organized by code
        system for section-aware matching, and a flat set is maintained for sections with no
        entry matching rules.

        Args:
            payload: The ConfigurationPayload containing the DbConfiguration and its
                     related DbConditions.

        Returns:
            ProcessedConfiguration: An object containing both flat and structured code sets.
        """

        # STEP 1: build per-system dicts from condition codes
        # each condition has snomed_codes, loinc_codes, icd10_codes, rxnorm_codes
        # each code object in those lists has .code and .display
        coding_by_code_system: dict[str, list[dict]] = defaultdict(list)
        for condition in payload.conditions:
            # map each db code list to its target dict + OID
            code_system_map: dict[CodeSystem, list] = (
                index_condition_code_list_by_system(condition)
            )

            for code_system, code_list in code_system_map.items():
                coding_by_code_system[
                    CodeSystem(code_system).format_system_string()
                ].extend(
                    [
                        asdict(
                            Coding(
                                code=c.code, display=c.display, system=code_system.oid
                            )
                        )
                        for c in code_list
                    ]
                )

        # STEP 2: add custom codes, routing by their system label
        for custom_code in payload.configuration.custom_codes:
            cur_code_system = CodeSystem(custom_code.system).format_system_string()
            code_val = custom_code.code
            display_val = custom_code.name

            # route to the correct dict based on system label
            coding_by_code_system[cur_code_system].append(
                asdict(
                    Coding(
                        code=code_val,
                        display=display_val,
                        system=CodeSystem(cur_code_system).oid,
                    )
                )
            )

        # STEP 3: build the CodeSystemSets
        code_system_sets = CodeSystemSets.from_dict(data=coding_by_code_system)

        # STEP 4: build included_condition_rsg_codes
        included_condition_rsg_codes = set()
        for c in payload.conditions:
            included_condition_rsg_codes.update(c.child_rsg_snomed_codes)

        return cls(
            codes=code_system_sets.all_codes,
            code_system_sets=code_system_sets,
            section_processing=[
                asdict(section) for section in payload.configuration.section_processing
            ],
            included_condition_rsg_codes=included_condition_rsg_codes,
        )

from dataclasses import asdict, dataclass, field

from pydantic import BaseModel, Field

from ..db.conditions.model import DbCondition
from ..db.configurations.model import DbConfiguration

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Payload` class (e.g., ConfigurationPayload) holds raw DB models.
# 2. A `Processed` class (e.g., ProcessedConfiguration) holds the final, ready-to-use data.
# 3. The `Processed` class has a `.from_payload()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================


# NOTE:
# CODE SYSTEM MODELS
# =============================================================================

SYSTEM_LABEL_TO_OID: dict[str, str] = {
    "SNOMED": "2.16.840.1.113883.6.96",
    "LOINC": "2.16.840.1.113883.6.1",
    "ICD-10": "2.16.840.1.113883.6.90",
    "RxNorm": "2.16.840.1.113883.6.88",
    "CVX": "2.16.840.1.113883.12.292",
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

    # OID → attribute name mapping for system-aware lookup
    _OID_TO_ATTR: dict[str, str] = field(
        default_factory=lambda: {
            "2.16.840.1.113883.6.96": "snomed",
            "2.16.840.1.113883.6.1": "loinc",
            "2.16.840.1.113883.6.90": "icd10",
            "2.16.840.1.113883.6.88": "rxnorm",
            "2.16.840.1.113883.12.292": "cvx",
        },
        repr=False,
    )

    @property
    def all_codes(self) -> set[str]:
        """
        Flat set of all code strings across all systems.

        Use this for sections that don't have entry_match_rules
        defined yet (the old generic search path).
        """

        return (
            set(self.snomed)
            | set(self.loinc)
            | set(self.icd10)
            | set(self.rxnorm)
            | set(self.cvx)
            | set(self.other)
        )

    def _get_system_dict(self, code_system_oid: str) -> dict[str, Coding] | None:
        """
        Resolve an OID to the corresponding code system dict.

        Args:
            code_system_oid: The code system OID to resolve.

        Returns:
            The dict for that system, or None if the OID is unknown.
        """

        attr_name = self._OID_TO_ATTR.get(code_system_oid)
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
        for system_dict in [
            self.snomed,
            self.loinc,
            self.icd10,
            self.rxnorm,
            self.cvx,
            self.other,
        ]:
            if code in system_dict:
                return system_dict[code]
        return None

    def has_match(self, code: str, code_system_oid: str | None = None) -> bool:
        """
        Check if a code matches without returning the full Coding.

        Convenience method for cases where you only need a boolean.
        """

        return self.find_match(code, code_system_oid) is not None


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

    configuration: DbConfiguration
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
    """

    codes: set[str] = Field(min_length=1)
    sections: list[Section]
    included_condition_rsg_codes: set[str]


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

        Args:
            data (dict): Input dictionary with required data.

        Returns:
            ProcessedConfiguration: A ProcessedConfiguration built from the dictionary.
        """

        validated = ProcessedConfigurationData.model_validate(data)

        # from_dict only has a flat set of codes — no code system info available
        # put everything into 'other' since we don't know the systems
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
        snomed: dict[str, Coding] = {}
        loinc: dict[str, Coding] = {}
        icd10: dict[str, Coding] = {}
        rxnorm: dict[str, Coding] = {}
        cvx: dict[str, Coding] = {}
        other: dict[str, Coding] = {}

        for condition in payload.conditions:
            # map each db code list to its target dict + OID
            system_mappings: list[tuple[list, dict[str, Coding], str]] = [
                (condition.snomed_codes, snomed, "2.16.840.1.113883.6.96"),
                (condition.loinc_codes, loinc, "2.16.840.1.113883.6.1"),
                (condition.icd10_codes, icd10, "2.16.840.1.113883.6.90"),
                (condition.rxnorm_codes, rxnorm, "2.16.840.1.113883.6.88"),
            ]

            for code_list, target_dict, oid in system_mappings:
                for code_obj in code_list:
                    if code_obj.code not in target_dict:
                        target_dict[code_obj.code] = Coding(
                            code=code_obj.code,
                            display=getattr(code_obj, "display", ""),
                            system=oid,
                        )

        # STEP 2: add custom codes, routing by their system label
        for custom_code in payload.configuration.custom_codes:
            system_label = custom_code.system
            code_val = custom_code.code
            display_val = custom_code.name

            oid = SYSTEM_LABEL_TO_OID.get(system_label, "")

            # route to the correct dict based on system label
            target_map: dict[str, dict[str, Coding]] = {
                "SNOMED": snomed,
                "LOINC": loinc,
                "ICD-10": icd10,
                "RxNorm": rxnorm,
                "CVX": cvx,
            }
            target_dict = target_map.get(system_label, other)

            if code_val not in target_dict:
                target_dict[code_val] = Coding(
                    code=code_val,
                    display=display_val,
                    system=oid if oid else system_label,
                )

        # STEP 3: build the CodeSystemSets
        code_system_sets = CodeSystemSets(
            snomed=snomed,
            loinc=loinc,
            icd10=icd10,
            rxnorm=rxnorm,
            cvx=cvx,
            other=other,
        )

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

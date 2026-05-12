from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field, fields
from typing import ClassVar

from pydantic import BaseModel, Field

from app.db.code_systems.db import CodeSystemName, DbCodeSystem, get_all_code_systems_db
from app.db.pool import AsyncDatabaseConnection

from ..db.conditions.model import DbCondition, DbConditionCoding

# NOTE:
# This file establishes a consistent pattern for handling terminology data:
# 1. A `Processed` class (e.g., ProcessedConfiguration) holds the final, ready-to-use data.
# 2. The `Processed` class has a `.from_dict()` factory method that contains all
#    the logic to transform the raw payload into the processed version.
# This separates data fetching, data processing, and data usage into clean, testable steps.
# =============================================================================


# CODE SYSTEM MODELS
# =============================================================================
class SupportedCodeSystems(BaseModel):
    """
    An registry for code system data that pulls values from the db.
    """

    _registry: ClassVar[dict[CodeSystemName, DbCodeSystem]] = {}

    @classmethod
    async def load_from_db(cls, db: AsyncDatabaseConnection):
        """Initialize registry from the database table call."""

        systems = await get_all_code_systems_db(db)
        cls._registry = systems

    @classmethod
    def get_or_raise(cls, name: str) -> DbCodeSystem:
        """
        Get a specific code system based on its name.
        """

        string_to_search = name.strip().lower()
        sanitized = cls.get(string_to_search)
        if not sanitized:
            # try falling back to display name
            sanitized = cls.get_by_display_name(string_to_search)

            if not sanitized:
                raise ValueError(
                    f"Requested code system {name} not found. Allowed code system must be one of: {cls.allowed()}"
                )

        return sanitized

    @classmethod
    def get(cls, name: str) -> DbCodeSystem | None:
        """
        Get a specific code system based on its name.
        """

        return cls._registry.get(name)

    @classmethod
    def get_by_oid(cls, oid: str) -> DbCodeSystem | None:
        """
        Get a specific code system based on its name.
        """
        value = [system for system in cls._registry.values() if system.oid == oid]
        if len(value) > 1:
            raise ValueError("OID didn't uniquely identify system information")
        if len(value) == 0:
            return None

        return value[0]

    @classmethod
    def get_by_display_name(cls, display_name: str) -> DbCodeSystem | None:
        """
        Get a specific code system based on its display name.
        """
        value = [
            system_data
            for system_data in cls._registry.values()
            if system_data.display_name == display_name
        ]
        if len(value) > 1:
            raise ValueError("Display name matched multiple code systems")
        if len(value) == 0:
            return None

        return value[0]

    @classmethod
    def all(cls) -> list[DbCodeSystem]:
        """
        Get all code system values.
        """

        return list(cls._registry.values())

    @classmethod
    def allowed(cls):
        """
        Get all allowed names for supported systems.
        """

        return list(cls._registry.keys())


def index_condition_code_list_by_system(
    condition: DbCondition,
) -> dict[CodeSystemName, list[DbConditionCoding]]:
    """
    Utility method to index condition code lists as stored into the DB by the system enum values. Useful for various processing jobs processing.
    """

    result: dict[CodeSystemName, list[DbConditionCoding]] = defaultdict(list)
    for s in SupportedCodeSystems.all():
        condition_column_index = f"{s.display_name}_codes"
        result[s.name] = getattr(condition, condition_column_index, [])

    return result


ALLOWED_CUSTOM_CODE_SYSTEM_NAMES = ", ".join(
    item.display_name for item in SupportedCodeSystems.all()
)


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

        attr_name = SupportedCodeSystems.get_by_oid(code_system_oid)
        if attr_name is None:
            return None
        return getattr(self, attr_name.name)

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

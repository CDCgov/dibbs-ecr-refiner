from dataclasses import dataclass, field
from typing import Literal, TypedDict


@dataclass
class ReportableCondition:
    """
    Object to hold the properties of a reportable condition.
    """

    code: str
    display_name: str


@dataclass
class JurisdictionReportableConditions:
    """
    Object to hold all reportable conditions for a given jurisdiction.
    """

    jurisdiction: str
    conditions: list[ReportableCondition]


class ProcessedRR(TypedDict):
    """
    The returned result of processing an RR.
    """

    reportable_conditions: list[JurisdictionReportableConditions]


@dataclass
class RefinedDocument:
    """
    Object to hold a reportable condition and its refined eICR and RR XML strings.
    """

    reportable_condition: ReportableCondition
    refined_eicr: str
    refined_rr: str


@dataclass
class RefinementPlan:
    """
    A complete, actionable plan for refining a single eICR document.

    This object serves as the contract between the orchestration layer (which
    knows about databases and business logic) and the pure refinement service
    (which only knows how to manipulate XML). This is the final form of the
    ProcessedConfiguration, as it combines the complete set of XPaths used in
    the filtering process with the joined set of section processing instructions
    that result from the configuration's instructions and the sections that appear
    in the eICR document after an initial scan.
    """

    xpath: str
    section_instructions: dict[str, Literal["retain", "refine", "remove"]]


# NOTE:
# STATIC SPECIFICATION MODELS
# =============================================================================


@dataclass(frozen=True)
class TriggerCode:
    """
    Represents a specific trigger code definition within a section.
    """

    oid: str
    display_name: str
    element_tag: str  # e.g., "observation", "act", "manufacturedProduct"


@dataclass(frozen=True)
class SectionSpecification:
    """
    Represents the static rules for a specific section in the eICR specification.
    """

    loinc_code: str
    display_name: str
    template_id: str
    trigger_codes: list[TriggerCode] = field(default_factory=list)

    @property
    def trigger_oids(self) -> set[str]:
        """
        Returns a set of all trigger code OIDs for O(1) lookup.
        """

        return {tc.oid for tc in self.trigger_codes}


@dataclass(frozen=True)
class EICRSpecification:
    """
    Represents the full static specification for a specific eICR version.
    """

    version: str
    sections: dict[str, SectionSpecification]

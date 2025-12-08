from dataclasses import dataclass
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


@dataclass(frozen=True)
class TriggerCode:
    """
    Represents a specific trigger code definition within a section.
    """

    oid: str  # The full templateId (root or root:extension)
    display_name: str
    element_tag: str  # e.g., "observation", "act", "manufacturedProduct"


@dataclass(frozen=True)
class SectionSpecification:
    """
    Static definition of an eICR section for a specific version.
    """

    loinc_code: str
    display_name: str
    template_id: str  # The section's templateId OID
    trigger_codes: list[TriggerCode]

    @property
    def trigger_oids(self) -> set[str]:
        """
        Returns a set of all trigger OIDs for O(1) lookup during processing.
        """

        return {tc.oid for tc in self.trigger_codes}


@dataclass(frozen=True)
class EICRSpecification:
    """
    The complete static "Rulebook" for a specific eICR version (e.g., '1.1', '3.1').
    """

    version: str
    sections: dict[str, SectionSpecification]  # Keyed by LOINC code


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

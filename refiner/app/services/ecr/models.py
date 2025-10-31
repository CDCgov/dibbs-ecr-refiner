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

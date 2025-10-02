from dataclasses import dataclass
from typing import TypedDict


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
    Object to hold a reportable condition and its refined eICR XML string.
    """

    reportable_condition: ReportableCondition
    refined_eicr: str

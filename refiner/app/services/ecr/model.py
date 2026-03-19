from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypedDict

from app.db.configurations.model import DbConfigurationSectionInstructions

if TYPE_CHECKING:
    from app.services.terminology import CodeSystemSets

type NamespaceMap = dict[str, str]
type EicrVersion = Literal["1.1", "3.1", "3.1.1"]


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
class EICRRefinementPlan:
    """
    A complete, actionable plan for refining a single eICR document.

    This object serves as the contract between the orchestration layer (which
    knows about databases and business logic) and the pure refinement service
    (which only knows how to manipulate XML).

    Contains both:
    - codes_to_check: Flat set for the existing generic search path (backward compat)
    - code_system_sets: Structured per-system lookup for the new section-aware path

    Once all sections migrate to entry_match_rules, codes_to_check can be removed.
    """

    codes_to_check: set[str]
    code_system_sets: "CodeSystemSets"
    section_instructions: dict[str, DbConfigurationSectionInstructions]


@dataclass
class RRRefinementPlan:
    """
    Refinement plan for an RR.

    Only contains the child RSG SNOMED codes
    that should be retained in the reportability response.
    """

    included_condition_child_rsg_snomed_codes_to_retain: set[str]


# NOTE:
# STATIC SPECIFICATION MODELS
# =============================================================================


@dataclass(frozen=True)
class TriggerCode:
    """
    Represents a specific trigger code definition within a section.

    `element_tag` here means something like: "observation", "act",
    "manufacturedProduct"
    """

    oid: str
    display_name: str
    element_tag: str


@dataclass(frozen=True)
class EntryMatchRule:
    """
    Each <section> has its own rules for their <entry>s; this object memorializes those rules.
    """

    code_xpath: str
    code_system_oid: str | None = None
    translation_xpath: str | None = None
    translation_code_system_oid: str | None = None
    prune_container_xpath: str | None = None


@dataclass(frozen=True)
class SectionSpecification:
    """
    Represents the static rules for a specific section in the eICR specification.
    """

    loinc_code: str
    display_name: str
    template_id: str
    trigger_codes: list[TriggerCode] = field(default_factory=list)
    entry_match_rules: list[EntryMatchRule] = field(default_factory=list)

    @property
    def trigger_oids(self) -> set[str]:
        """
        Returns a set of all trigger code OIDs for O(1) lookup.
        """

        return {tc.oid for tc in self.trigger_codes}

    @property
    def has_match_rules(self) -> bool:
        """
        Does the section have entry matching rules or not?

        Returns `True`, that the section **has** entry matching rules; or, `False`,
        the section **doesn't have** entry matching rules.
        """

        return len(self.entry_match_rules) > 0


@dataclass(frozen=True)
class EICRSpecification:
    """
    Represents the full static specification for a specific eICR version.
    """

    version: str
    sections: dict[str, SectionSpecification]

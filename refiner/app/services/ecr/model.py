from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Final, Literal, TypedDict

from app.db.configurations.model import DbConfigurationSectionInstructions

if TYPE_CHECKING:
    from app.services.terminology import CodeSystemSets

# NOTE:
# NAMESPACE CONSTANTS
# =============================================================================

type NamespaceMap = dict[str, str]

HL7_NAMESPACE: Final[str] = "urn:hl7-org:v3"

HL7_NS: Final[NamespaceMap] = {"hl7": HL7_NAMESPACE}

HL7_XSI_NS: Final[NamespaceMap] = {
    "hl7": HL7_NAMESPACE,
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


# NOTE:
# VERSION TYPE
# =============================================================================

type EicrVersion = Literal["1.1", "3.1", "3.1.1"]


# NOTE:
# REPORTABLE CONDITION MODELS
# =============================================================================


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

    Rules are evaluated in list order with structural precedence: if a
    rule's code_xpath finds code-bearing elements in an entry (candidates),
    that rule claims the entry regardless of whether any codes matched —
    subsequent rules are not evaluated. This prevents fallback rules from
    running on entries that were already examined by a more specific rule.

    Attributes:
        code_xpath:
            XPath expression (relative to <entry>) targeting the primary
            code-bearing elements for this rule. Should be scoped to a
            specific C-CDA templateId predicate where possible so that
            structural precedence operates at the template level rather
            than the element level.

        code_system_oid:
            OID of the expected code system for primary code matches.
            When set, only codes whose configured code system matches
            this OID are considered matches. When None, any code system
            is accepted — use None when vendor coding practice is too
            varied to rely on the codeSystem attribute, and document
            the intent with a comment at the call site.

            For rules where the OID encodes semantic meaning (e.g.
            SNOMED_OID on observation/value means "organism/substance
            result codes specifically"), retain the OID and document
            why. For rules where the OID is a validity guard on a
            structurally unambiguous location (e.g. RxNorm on
            manufacturedMaterial/code), None is acceptable because the
            XPath already constrains the match location sufficiently.

        translation_xpath:
            XPath expression targeting translation elements to check
            when the primary code_xpath produces no match. Handles the
            common real-world pattern where the IG-expected code system
            appears in <translation> rather than at the primary
            location (e.g. local code as primary, LOINC in translation).

        translation_code_system_oid:
            OID for translation code matching. Same semantics as
            code_system_oid. When None, any code system in the
            translation is accepted.

        prune_container_xpath:
            XPath expression (relative to <entry>) identifying the
            container elements to prune within a matched entry. When
            set, only containers that contain a matched code element
            are kept; the rest are removed. When None, the matched
            entry is kept whole — no intra-entry pruning is performed.

            Used for sections where entries contain panels of
            sub-observations (Results organizer/component, Vital Signs
            organizer/component) and each sub-observation should be
            individually retained or removed.

        require_value_set_attr:
            When True, a code element only qualifies as a match
            candidate if it also carries an sdtc:valueSet attribute.

            This guard is specifically for result observation value
            elements where the presence of sdtc:valueSet is the
            structural indicator that a code was placed there as an
            RCTC trigger code rather than as a plain clinical finding
            value. Per CONF:4527-443 (STU 3.1.1), sdtc:valueSet SHALL
            be present on genuine trigger code values.

            Without this guard, generic SNOMED qualifier codes like
            260373001 "Detected (qualifier value)" — which appear as
            plain observation values on any positive test — would match
            the organism/substance rule and cause unrelated result
            entries to be retained. The sdtc:valueSet attribute is
            absent on those elements, so the guard correctly filters
            them out while still matching codes like 5247005 "Bordetella
            pertussis (organism)" that are genuine RCTC trigger values
            and do carry sdtc:valueSet.

            Default False. Only set to True on rules targeting
            observation/value where this distinction matters.

        tier:
            IG conformance tier for this rule. Used in match provenance
            comments to indicate how the rule relates to the spec:

                1 — SHALL: directly mandated by the IG. The primary
                    conformant path. If a sender follows the spec, this
                    rule matches.

                2 — SHOULD/MAY: permitted by the IG but not required.
                    Handles optional patterns (translations, alternate
                    code locations) that conformant senders may or may
                    not use.

                3 — HEURISTIC: not IG-conformant but observed in real
                    EHR output. Accommodates vendor variance. Each tier
                    3 rule should carry a comment explaining what
                    real-world pattern it was written for.

            Surfaces in XML match comments as (T1), (T2), or (T3) so
            readers can immediately tell whether a match fired on a
            spec-mandated path or a heuristic accommodation.

            Default 1.

        preserve_whole_entry:
            When True, a matched entry is kept entirely intact —
            all child elements including entryRelationship chains,
            performers, authors, participants, and nested clinical
            statements are preserved without pruning.

            Use this for clinical acts where the entry is the natural
            unit of preservation and intra-entry pruning would destroy
            clinical meaning. The canonical cases are:

              - Medication Activity: entryRelationship[@typeCode='CAUS']
                carries Reaction Observation (V2) — adverse event
                information that belongs with the medication record
                per CONF:1098-7552 (MAY, Medication Activity V2).
              - Procedure Activity: entryRelationship[@typeCode='COMP']
                carries Reaction Observation (V2) per CONF:1098-32475
                (MAY, Procedure Activity Procedure V2).
              - Immunization Activity: entryRelationship carries
                Reaction Observation (V2) per the Immunization Activity
                V3 template context table.
              - Social History structured entries (Travel History,
                Exposure, Occupation): all meaningful content lives in
                <participant> and nested entryRelationships, not in the
                top-level coded elements. Preserving only the match path
                would strip the location, employer, or agent information
                that makes the entry useful to the PHA.

            When True, prune_container_xpath is ignored — there is no
            intra-entry pruning to perform. The match fires, the entry
            is kept whole.

            Default False.
    """

    code_xpath: str
    code_system_oid: str | None = None
    translation_xpath: str | None = None
    translation_code_system_oid: str | None = None
    prune_container_xpath: str | None = None
    require_value_set_attr: bool = False
    tier: int = 1
    preserve_whole_entry: bool = False


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


# NOTE:
# PROVENANCE MODELS
# =============================================================================


class SectionSource(StrEnum):
    """
    Describes how a section's processing instructions were determined.

    Used in SectionProvenanceRecord to explain why a section in the refined
    eICR looks the way it does.

    Values:
        CONFIGURED:   The jurisdiction explicitly configured this section in
                      the application. Instructions reflect their choices.
        SYSTEM_SKIP:  The section is in SECTION_PROCESSING_SKIP — a hardcoded
                      set of sections that are always retained regardless of
                      jurisdiction configuration (e.g., emergency outbreak info,
                      reportability response info).
        UNCONFIGURED: The section was present in the source document but absent
                      from the jurisdiction's configuration. Falls back to
                      SKIP_SECTION_INSTRUCTIONS (include=True, retain) so the
                      section is preserved intact.
    """

    CONFIGURED = "configured"
    SYSTEM_SKIP = "system_skip"
    UNCONFIGURED = "unconfigured"


class SectionOutcome(StrEnum):
    """
    Describes what the refiner actually did to a section at runtime.

    Distinct from the configured action and narrative settings, which
    describe what the jurisdiction asked for. Most outcomes confirm the
    configuration; one (REFINED_NO_MATCHES_STUBBED) reflects a refiner
    policy override that fires when filtering removes everything from
    a section configured for refinement.

    The seven outcomes cover the full configuration space (current and
    future):

        REMOVED_BY_CONFIG:
            include=False. Section reduced to a minimal stub regardless
            of action/narrative settings.

        RETAINED:
            include=True, action="retain", narrative="retain". Section
            left untouched.

        RETAINED_NARRATIVE_REMOVED:
            include=True, action="retain", narrative="remove". Entries
            kept as provided, narrative replaced with the removal notice.

        REFINED_WITH_MATCHES:
            include=True, action="refine", narrative="retain". Entries
            filtered to those matching the configuration, original
            narrative preserved for context.

        REFINED_NARRATIVE_REMOVED:
            include=True, action="refine", narrative="remove". Entries
            filtered, narrative replaced with the removal notice.

        REFINED_NARRATIVE_RECONSTRUCTED:
            include=True, action="refine", narrative="refine" (future).
            Entries filtered, narrative reconstructed from surviving
            entries. Not yet reachable — depends on narrative
            reconstruction work landing.

        REFINED_NO_MATCHES_STUBBED:
            include=True, action="refine", any narrative setting. The
            policy override: when filtering finds nothing, the section
            is stubbed regardless of narrative configuration. Applies
            uniformly to all three "refine" variants.

    The combination (action="retain", narrative="refine") is invalid
    because narrative reconstruction requires refined entries to build
    from; the configuration UI prevents it and there is no corresponding
    outcome.
    """

    REMOVED_BY_CONFIG = "removed_by_config"
    RETAINED = "retained"
    RETAINED_NARRATIVE_REMOVED = "retained_narrative_removed"
    REFINED_WITH_MATCHES = "refined_with_matches"
    REFINED_NARRATIVE_REMOVED = "refined_narrative_removed"
    REFINED_NARRATIVE_RECONSTRUCTED = "refined_narrative_reconstructed"
    REFINED_NO_MATCHES_STUBBED = "refined_no_matches_stubbed"


@dataclass(frozen=True)
class SectionProvenanceRecord:
    """
    Documents how a single section was processed during refinement.

    Built during plan creation (create_eicr_refinement_plan) when the
    configuration-derived fields can be populated. The runtime
    `outcome` field is populated later, after section processing
    completes — refine_eicr uses `dataclasses.replace` to produce a
    finalized record before passing it to the footnote appender.

    The record drives the per-section provenance footnote in the
    refined output, giving jurisdiction reviewers and downstream
    systems a clear explanation of why each section looks the way it
    does in the refined output.

    Attributes:
        loinc_code:     The section's LOINC code (e.g., "46240-8").
        display_name:   Human-readable section name. For configured sections,
                        this is the jurisdiction's name from the configuration
                        (what they see in the UI). For system_skip and
                        unconfigured sections, this is the IG canonical name
                        from the section catalog.
        include:        Whether the section was configured for inclusion.
                        False means the section was configured for wholesale
                        removal regardless of action.
        action:         The configured processing action: "refine" or "retain".
        narrative:      Whether the original narrative <text> was configured
                        to be preserved. Currently a bool; will become a
                        three-way enum ("retain"/"remove"/"refine") when
                        narrative reconstruction lands.
        config_version: The version number of the activated configuration used
                        for this refinement run. None if not available (e.g.,
                        legacy S3 configs that predate version tracking).
        source:         How the processing instructions were determined —
                        configured by the jurisdiction, held by a system rule,
                        or unconfigured (fell back to retain).
        outcome:        What the refiner actually did to this section at
                        runtime. Distinct from the configured action because
                        of the no-match policy override. Set during
                        refine_eicr after section processing completes;
                        defaults to a sentinel that should never appear in a
                        rendered footnote.
    """

    loinc_code: str
    display_name: str
    include: bool
    action: str
    narrative: bool
    config_version: int | None
    source: SectionSource
    outcome: SectionOutcome = SectionOutcome.REFINED_WITH_MATCHES


# NOTE:
# REFINEMENT PLAN MODELS
# =============================================================================


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

    The specification, section_provenance, config_version, and
    augmentation_timestamp fields are built during plan creation so that
    refine_eicr is a pure executor: given a plan, execute it, with no
    document introspection or spec loading needed at runtime.

    Attributes:
        codes_to_check: Flat set of all condition codes used by the generic
            fallback matching path.
        code_system_sets: Structured per-system lookup used by the section-aware
            matching path. Carries display names for enrichment.
        section_instructions: Per-section processing instructions keyed by
            LOINC code. Drives the branch logic in refine_eicr (refine,
            retain, remove, narrative-removed).
        section_provenance: Per-section provenance records keyed by LOINC
            code. Consumed by the footnote appender after each section is
            processed. Records have placeholder `outcome` fields at plan
            creation time; refine_eicr finalizes the outcome before
            rendering each footnote.
        specification: The fully resolved eICR specification for the
            document's version. Provides section catalog and entry match
            rules to the section-aware processing path.
        config_version: The version number of the activated configuration
            used for this refinement run. None for legacy configurations
            that predate version tracking.
        augmentation_timestamp: The HL7 V3 timestamp (format
            "YYYYMMDDHHMMSS±ZZZZ") from the AugmentationContext shared
            across this refinement run. Used to stamp both the augmentation
            author's <time> value and the IDs on per-section provenance
            footnotes, giving the two a structural consistency a consumer
            can verify. Required — every refinement run has a timestamp.
    """

    codes_to_check: set[str]
    code_system_sets: "CodeSystemSets"
    section_instructions: dict[str, DbConfigurationSectionInstructions]
    section_provenance: dict[str, SectionProvenanceRecord]
    specification: EICRSpecification
    augmentation_timestamp: str
    config_version: int | None = None


@dataclass
class RRRefinementPlan:
    """
    Refinement plan for an RR.

    Only contains the child RSG SNOMED codes
    that should be retained in the reportability response.
    """

    included_condition_child_rsg_snomed_codes_to_retain: set[str]


# NOTE:
# SECTION PROCESSING RESULTS
# =============================================================================


@dataclass(frozen=True)
class SectionRunResult:
    """
    What the section processing engines actually did at runtime.

    Returned by `entry_matching.process` and `generic_matching.process`
    (and surfaced through the `process_section` dispatcher) so that
    `refine.py` can map the structural facts to a user-facing
    `SectionOutcome` for the provenance footnote.

    The split between this dataclass and `SectionOutcome` is
    deliberate: the matching engines report **facts** (whether matches
    were found, what they did to the narrative), and the orchestrator
    interprets those facts into the user-facing outcome name. Keeping
    interpretation out of the engines means the matching code stays
    structural and any future policy decisions about how to label
    outcomes can land in one place (refine._interpret_run_result)
    without touching the engines.

    Attributes:
        matches_found: True if the matching step found at least one
            entry to keep. False if the section ended up stubbed
            because filtering removed everything.
        narrative_disposition: What the engine did with the section's
            <text> element when matches were found. Meaningless when
            matches_found is False — the engine stubs the entire
            section and the consumer in refine.py short-circuits before
            reading this field. Defaulted to "retained" in the no-match
            case as a placeholder.
    """

    matches_found: bool
    narrative_disposition: Literal["retained", "removed", "reconstructed"]

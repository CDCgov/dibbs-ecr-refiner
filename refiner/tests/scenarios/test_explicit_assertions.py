import json
from typing import Final

from lxml import etree

from app.core.models.types import XMLFiles
from app.services.terminology import ProcessedConfiguration

from ..fixtures.loader import load_fixture_str
from .harness import refine_one

# NOTE:
# SHARED CONTEXT
# =============================================================================
# mirrors what `test_all_sections_covid_flu.py`'s covid_baseline scenario
# loads, inlined here to keep this file self-contained; explicit tests
# should be readable in isolation--someone debugging an issue #5
# regression shouldn't need to cross-reference another file to know
# what's being loaded

FIXTURE_DIR: Final[str] = "all_sections_COVID_INFLUENZA"
COVID_BASELINE_CONFIG: Final[str] = "covid_baseline.json"

COVID_RSG_CODE: Final[str] = "840539006"
COVID_CANONICAL_URL: Final[str] = (
    "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
    "07221093-b8a1-4b1d-8678-259277bfba64"
)
JURISDICTION: Final[str] = "SDDH"
CONFIGURATION_VERSION: Final[int] = 1

HL7_NS: Final[dict[str, str]] = {"hl7": "urn:hl7-org:v3"}


# NOTE:
# ROLL-UP ISSUE #5 - NEGATIVE CASE
# =============================================================================
# procedures must not be retained based on an entryRelationship code match
# alone; the fixture sets up the precise three-way condition described in
# the original roll-up sheet:
#
#   1. nausea (SNOMED 422587007) is in the COVID condition grouper
#   2. the fixture's three procedure entries each carry nausea in their
#      entryRelationship
#   3. the matcher's structural-precedence rule requires a match at an
#      entry-level location to retain the entry; matches found only in
#      entryRelationship descendants must not, on their own, justify
#      retention
#
# the covid_baseline snapshot pins outcome (3) implicitly: this test
# pins it explicitly, with preconditions on (1) and (2) that fail
# diagnostically if either drifts

NAUSEA_CODE: Final[str] = "422587007"
PROCEDURES_LOINC: Final[str] = "47519-4"


def test_covid_baseline_does_not_retain_procedures_via_entry_relationship_only_match() -> (
    None
):
    """
    Explicit assertion of Roll-up Issue #5 (negative case).

    Three checks in order:

      1. Precondition: Nausea is in the COVID configuration's matchable
         codes. If not, this test no longer exercises Issue #5; fails
         diagnostically rather than passing for the wrong reason.
      2. Precondition: the source fixture has Nausea in the
         entryRelationship of one or more procedure entries. If not,
         the negative case isn't present in the data.
      3. Assertion: the refined Procedures section retains zero entries.
         If not, the matcher is retaining procedures via entryRelationship
         matches alone - a regression of Issue #5.
    """

    xml_files = XMLFiles(
        eicr=load_fixture_str(f"{FIXTURE_DIR}/eICR.xml"),
        rr=load_fixture_str(f"{FIXTURE_DIR}/RR.xml"),
    )
    processed_configuration = ProcessedConfiguration.from_dict(
        json.loads(
            load_fixture_str(f"{FIXTURE_DIR}/configurations/{COVID_BASELINE_CONFIG}")
        )
    )

    # precondition 1:
    # nausea must be a matchable code in the configuration:
    # * using the flat `codes` list since membership semantics are simple
    # and OID-agnostic; if `codes` ever becomes a different shape, the
    # AttributeError points at this assumption directly
    assert NAUSEA_CODE in processed_configuration.codes, (
        f"Nausea (SNOMED {NAUSEA_CODE}) is not in the COVID configuration's "
        f"matchable codes. This test no longer exercises Roll-up Issue #5's "
        f"negative case (which depends on the entryRelationship code being a "
        f"configured match). Either restore Nausea to the configuration "
        f"({COVID_BASELINE_CONFIG}) or remove this test."
    )

    # precondition 2:
    # source fixture must have Nausea in Procedures'
    # entryRelationship at least once
    source_root = etree.fromstring(xml_files.eicr.encode("utf-8"))
    nausea_in_procedures_er = source_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROCEDURES_LOINC}']"
        f"//hl7:entryRelationship//hl7:*[@code='{NAUSEA_CODE}']",
        namespaces=HL7_NS,
    )
    assert len(nausea_in_procedures_er) > 0, (
        f"Source fixture's Procedures section ({PROCEDURES_LOINC}) no longer "
        f"has Nausea (SNOMED {NAUSEA_CODE}) in any entryRelationship. The "
        f"negative case of Issue #5 isn't present in the data. Either restore "
        f"the fixture ({FIXTURE_DIR}/eICR.xml) or remove this test."
    )

    # assertion: refined procedures section retains zero entries
    result = refine_one(
        xml_files=xml_files,
        processed_configuration=processed_configuration,
        jurisdiction_code=JURISDICTION,
        rsg_code=COVID_RSG_CODE,
        canonical_url=COVID_CANONICAL_URL,
        configuration_version=CONFIGURATION_VERSION,
    )

    refined_root = etree.fromstring(result.refined_eicr.encode("utf-8"))
    refined_procedure_entries = refined_root.xpath(
        f".//hl7:section[hl7:code/@code='{PROCEDURES_LOINC}']/hl7:entry",
        namespaces=HL7_NS,
    )
    assert len(refined_procedure_entries) == 0, (
        f"Refined Procedures section retains {len(refined_procedure_entries)} "
        f"entries under covid_baseline. Roll-up Issue #5 regression: the "
        f"matcher is retaining procedures based on an entryRelationship match "
        f"that should not alone justify retention. The source fixture has "
        f"Nausea (SNOMED {NAUSEA_CODE}) in {len(nausea_in_procedures_er)} "
        f"entryRelationship location(s) inside procedures; with Nausea also "
        f"in the configured codes, this is exactly the scenario the original "
        f"Roll-up sheet flagged. Expected: 0 procedure entries retained."
    )

"""Inputs for refinement baseline generation and comparison.

Paths are relative to FIXTURE_DIR. When a pair has an ``archive``, its
``eicr`` and ``rr`` paths name members inside that ZIP instead. Keep archive
pairs even when their contents duplicate loose fixtures so both sources remain
accounted for.

Pair outputs use the fixture's top-level source directory, manifest name, and
scenario name from ``parity/cases.json``. Each scenario identifies a jurisdiction
and condition, for example ``UT_covid_19``. Its outputs are:
``expected/<source-directory>/<pair-name>/<scenario-name>/eICR.xml``
and ``RR.xml`` in the same directory. Source directories are ``ecr_pairs``,
``eicr_v1_1``, or ``eicr_v3_1_1``; ZIP members use their archive's source directory.

SECTION_FIXTURES lists bare sections processed directly with reconstruction under
the harness's fixed versions: 1.1, 3.1, and 3.1.1. Outputs use
``expected/sections/<name>/<version>/section.xml``.
Exclude ``expected/`` from input discovery; it contains generated outputs.

``parity/cases.json`` records section LOINCs and code sets, plus pair refinement
contexts and configuration-file references.
The referenced configuration payloads live under ``parity/configurations/``.
"""

from pathlib import Path
from typing import NotRequired, TypedDict

FIXTURE_DIR = Path(__file__).parent


class FixturePair(TypedDict):
    """A loose eICR/RR pair or two exact members of the same archive."""

    name: str
    eicr: str
    rr: str
    archive: NotRequired[str]


class SectionFixture(TypedDict):
    """A named standalone section fixture."""

    name: str
    path: str


PAIRS: list[FixturePair] = [
    # Loose XML pairs.
    {
        "name": "all_sections_covid_influenza",
        "eicr": "ecr_pairs/all_sections_covid_influenza/eICR.xml",
        "rr": "ecr_pairs/all_sections_covid_influenza/RR.xml",
    },
    {
        "name": "covid_influenza_v1_1",
        "eicr": "eicr_v1_1/mon_mothma_covid_influenza_eICR.xml",
        "rr": "eicr_v1_1/mon_mothma_covid_influenza_RR.xml",
    },
    {
        "name": "zika_v3_1_1",
        "eicr": "eicr_v3_1_1/mon_mothma_zika_eICR.xml",
        "rr": "eicr_v3_1_1/mon_mothma_zika_RR.xml",
    },
    {
        "name": "multi_condition_multi_covid",
        "eicr": "eicr_v3_1_1/multi-condition-multi-covid-CDA_eICR.xml",
        "rr": "eicr_v3_1_1/multi-condition-multi-covid-CDA_RR.xml",
    },
    {
        "name": "all_sections_v3_1_1",
        "eicr": "eicr_v3_1_1/all_sections_test_files/CDA_eICR.xml",
        "rr": "eicr_v3_1_1/all_sections_test_files/CDA_RR.xml",
    },
    # Archive pairs: member paths are case-sensitive and include nested folders.
    {
        "name": "covid_influenza_v1_1_zip",
        "archive": "eicr_v1_1/mon_mothma_covid_influenza_1.1.zip",
        "eicr": "mon_mothma_covid_influenza_1.1/CDA_eICR.xml",
        "rr": "mon_mothma_covid_influenza_1.1/CDA_RR.xml",
    },
    {
        "name": "zika_v3_1_1_zip",
        "archive": "eicr_v3_1_1/mon_mothma_zika_3.1.1.zip",
        "eicr": "CDA_eICR.xml",
        "rr": "CDA_RR.xml",
    },
    {
        "name": "all_sections_sddh_zip",
        "archive": "eicr_v3_1_1/all_sections_test_files/all_sections_SDDH.zip",
        "eicr": "all_sections_SDDH_jurisdiction_id/CDA_eICR.xml",
        "rr": "all_sections_SDDH_jurisdiction_id/CDA_RR.xml",
    },
    {
        "name": "all_sections_sddh_nonsense_problems_zip",
        "archive": (
            "eicr_v3_1_1/all_sections_test_files/"
            "all_sections_SDDH_nonsense_problems.zip"
        ),
        "eicr": "nonsense_problems/CDA_eICR.xml",
        "rr": "nonsense_problems/CDA_RR.xml",
    },
    {
        "name": "all_sections_test_zip",
        "archive": "eicr_v3_1_1/all_sections_test_files/all_sections_TEST.zip",
        "eicr": "CDA_eICR.xml",
        "rr": "CDA_RR.xml",
    },
]

SECTION_FIXTURES: list[SectionFixture] = [
    {
        "name": "immunizations_flat",
        "path": "sections/immunizations_flat.xml",
    },
    {
        "name": "medications_administered",
        "path": "sections/medications_administered.xml",
    },
    {
        "name": "medications_no_known_negated",
        "path": "sections/medications_no_known_negated.xml",
    },
    {
        "name": "plan_of_treatment_all_kinds",
        "path": "sections/plan_of_treatment_all_kinds.xml",
    },
    {
        "name": "problems_concern_with_two_observations",
        "path": "sections/problems_concern_with_two_observations.xml",
    },
    {
        "name": "problems_icd10_primary",
        "path": "sections/problems_icd10_primary.xml",
    },
    {
        "name": "results_organizer_three_components",
        "path": "sections/results_organizer_three_components.xml",
    },
    {
        "name": "results_partial_reconstruction",
        "path": "sections/results_partial_reconstruction.xml",
    },
    {
        "name": "results_two_panels",
        "path": "sections/results_two_panels.xml",
    },
    {
        "name": "results_vendor_organizer_components",
        "path": "sections/results_vendor_organizer_components.xml",
    },
]

IGNORED_ARCHIVE_MEMBER_PATTERNS: tuple[str, ...] = ("__MACOSX/*",)

from dataclasses import dataclass
from typing import Literal

import pytest
import pytest_asyncio
from fastapi import status

from app.core.models.types import XMLFiles
from app.db.configurations.model import DbConfigurationCustomCode
from app.services.terminology import ProcessedConfiguration

from ...fixtures.loader import load_fixture_str
from ..conftest import (
    assert_schematron_valid,
    assert_xsd_valid,
    validate_refined_xml,
)

# localstack S3 base for activation payloads; activation writes active.json to
#   {base}/{jurisdiction}/{cg_uuid}/{version}/active.json
# mirroring the path test_configurations.py reads back from after activating
SCENARIO_S3_CONFIG_BASE = "http://localhost:4566/local-config-bucket/configurations"


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Update the snapshot files we check against.
    """

    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help=(
            "Regenerate scenario snapshots from current refinement output "
            "instead of comparing against committed files. Use when "
            "refinement behavior legitimately changes."
        ),
    )


@pytest.fixture
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    """
    Whether the test run requested snapshot regeneration.
    """

    return bool(request.config.getoption("--update-snapshots"))


# NOTE:
# SCENARIO MODEL
# =============================================================================
# a scenario is a recipe for a configuration, not a pointer to a committed
# json file. both the parametrized snapshot suite and the explicit-assertion
# suite build their configurations from these recipes through the live api
# (see build_scenario_configuration), so there is a single authoring path and
# no committed active.json to drift


@dataclass(frozen=True)
class SectionOverride:
    """
    One section-processing change applied via update_section_processing.

    Only the fields set here are changed; anything left None keeps the
    section's seeded default. "Exclude a section" is include=False; "refine but
    drop the prose" is narrative="remove""; narrative-only sections are forced to
    action="retain" by the API regardless of what is passed.
    """

    current_code: str
    include: bool | None = None
    narrative: str | None = None #DbNarrativeAction; kept as str to avoid the import
    action: str | None = None  # DbSectionAction; kept as str to avoid the import


@dataclass(frozen=True)
class CustomCode:
    """
    One custom code added via add_custom_code.
    """

    code: str
    system: str
    name: str


@dataclass(frozen=True)
class Scenario:
    """
    One refinement scenario: the condition to configure for plus the
    customizations layered on top of the default configuration.

    name: parametrize id and snapshot subdirectory name.
    fixture_dir: directory under tests/fixtures/ holding eICR.xml / RR.xml.
    condition_name: the condition display_name the config is created for.
    rsg_code: the reportable SNOMED code recorded on the trace for
        observability; does NOT drive refinement.
    canonical_url: the TES condition grouper canonical_url. Asserted against
        the seeded condition at build time (drift guard) and threaded into the
        augmentation seed.
    configuration_version: arbitrary per-scenario discriminator. Recorded on
        the trace AND rendered into each section's provenance footnote, so it
        affects the refined XML.
    custom_codes / section_overrides / associated_conditions: the recipe
        applied to the default configuration before activation.
    """

    name: str
    fixture_dir: str
    condition_name: str
    rsg_code: str
    canonical_url: str
    configuration_version: int
    custom_codes: tuple[CustomCode, ...] = ()
    section_overrides: tuple[SectionOverride, ...] = ()
    associated_conditions: tuple[str, ...] = ()


SCENARIOS: list[Scenario] = [
    Scenario(
        name="covid_baseline",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=1,
    ),
    Scenario(
        name="influenza_baseline",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="Influenza",
        rsg_code="541131000124102",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "38475891-387a-4fa2-bbe9-1dc97ce415d1"
        ),
        configuration_version=2,
    ),
    Scenario(
        name="covid_with_custom_codes",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=3,
        custom_codes=(
            CustomCode(
                "2563008", "cvx", "Flucelvax Quadrivalent 2021-2022 Injectable Product"
            ),
            CustomCode(
                "10628911000119103",
                "snomed",
                "Gastroenteritis caused by Influenza A virus",
            ),
            CustomCode("233573008", "snomed", "Extracorporeal membrane oxygenation"),
            CustomCode("8867-4", "loinc", "Heart rate"),
        ),
    ),
    Scenario(
        name="covid_with_section_overrides",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=4,
        section_overrides=(
            SectionOverride(current_code="10154-3", include=False),
            SectionOverride(current_code="10164-2", include=False),
            SectionOverride(current_code="29299-5", include=False),
            SectionOverride(current_code="30954-2", narrative="remove"),
            SectionOverride(current_code="29762-2", action="retain"),
        ),
    ),
    Scenario(
        name="covid_plus_unrelated_condition",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=5,
        associated_conditions=("Agricultural Chemicals (Fertilizer) Poisoning",),
    ),
    Scenario(
        name="covid_with_substance_admin_custom_code",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=6,
        custom_codes=(CustomCode("1115699", "rxnorm", "Oseltamivir"),),
    ),
    Scenario(
        name="covid_with_multi_vital_sign_codes",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=7,
        custom_codes=(
            CustomCode("8867-4", "loinc", "Heart rate"),
            CustomCode("8480-6", "loinc", "Systolic blood pressure"),
            CustomCode("9279-1", "loinc", "Respiratory rate"),
        ),
    ),
    Scenario(
        name="covid_with_procedure_only_code",
        fixture_dir="ecr_pairs/all_sections_covid_influenza",
        condition_name="COVID-19",
        rsg_code="840539006",
        canonical_url=(
            "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
            "07221093-b8a1-4b1d-8678-259277bfba64"
        ),
        configuration_version=8,
        custom_codes=(CustomCode("385857005", "snomed", "Artificial respiration"),),
    ),
]

# name -> Scenario lookup for the explicit-assertion suite, which references
# specific scenarios by name rather than parametrizing over the whole list.
SCENARIOS_BY_NAME: dict[str, Scenario] = {s.name: s for s in SCENARIOS}


def load_scenario_xml_files(scenario: Scenario) -> XMLFiles:
    """
    Load the committed source eICR/RR pair for a scenario's fixture.

    The fixtures are inputs (committed XML); only the configuration is built
    through the API.
    """

    return XMLFiles(
        eicr=load_fixture_str(f"{scenario.fixture_dir}/eICR.xml"),
        rr=load_fixture_str(f"{scenario.fixture_dir}/RR.xml"),
    )


# NOTE:
# COMPOSED VALIDATION FIXTURE
# =============================================================================
# composes the three validation steps an integration test would run on a
# refined document into one call per (xml, doc_kind) pair. the underlying
# validators (validate_xml_string, validate_xml_string_xsd) and their
# session-cached xsd_schema are inherited from the parent integration


@pytest.fixture
def validate_refined_document(
    validate_xml_string,
    validate_xml_string_xsd,
):
    """
    Returns a callable that runs full validation on one refined document.

    Scenarios call this twice (once for the refined eICR, once for the
    refined RR) before snapshot operations so:

      - In compare mode, an invalid document fails the test with a
        clear validation error rather than as an opaque XML diff.
      - In --update-snapshots mode, an invalid document fails the test
        BEFORE the snapshot is overwritten, preventing invalid snapshots
        from being committed.

    Args (on the returned callable):
        xml_string: the refined document as a UTF-8 string.
        doc_kind: "eICR" or "RR" - used only for human-readable labels
            in failure messages; the actual document type is detected
            from the root template OID.
        scenario_name: included in failure messages and labels.
    """

    def _validate(
        xml_string: str,
        doc_kind: str,
        scenario_name: str,
    ) -> None:
        label = f"{scenario_name} {doc_kind}"

        # well-formedness + correct CDA ClinicalDocument root
        validate_refined_xml(xml_string, doc_kind, label, scenario_name)

        # CDA R2 XSD: schema is session-cached
        xsd_result = validate_xml_string_xsd(xml_string)
        assert_xsd_valid(xsd_result, label, scenario_name)

        # schematron - the XSLT is compiled per call
        schematron_result = validate_xml_string(xml_string, doc_kind.lower())
        assert_schematron_valid(schematron_result, label, scenario_name)

    return _validate


@pytest_asyncio.fixture
async def fetch_activation_payload(authed_client):
    """
    Returns a function that reads the active.json an activation wrote to
    localstack S3 and parses it into a ProcessedConfiguration.

    This is the disk-free replacement for the manual `awslocal s3 cp
    .../active.json` step the scenarios suite used to depend on: the config is
    authored through the API, activated (which writes active.json to S3 exactly
    as production does), then read back here in the same serialization the
    lambda path consumes.

    Version resolution: when `version` is None (the default), the active
    version is discovered from current.json, mirroring how lambda finds the
    active config. This keeps the helper correct when more than one config for
    the same condition is activated within a single test (the second
    activation is version 2, and so on) -- a hardcoded version=1 would silently
    return the first config in that case.

    payload = await fetch_activation_payload(
        jurisdiction_id="SDDH",
        canonical_url="https://.../ValueSet/<uuid>",
    )
    """

    async def _get(
        jurisdiction_id: str,
        canonical_url: str,
        version: int | None = None,
    ) -> ProcessedConfiguration:
        cg_uuid = canonical_url.rstrip("/").rsplit("/", 1)[-1]
        base = f"{SCENARIO_S3_CONFIG_BASE}/{jurisdiction_id}/{cg_uuid}"

        if version is None:
            current_resp = await authed_client.get(f"{base}/current.json")
            assert current_resp.status_code == status.HTTP_200_OK, (
                f"Could not read current.json at {base}/current.json "
                f"(status {current_resp.status_code})"
            )
            version = current_resp.json()["version"]
            assert version is not None, (
                f"current.json at {base} reports a null version -- the config "
                f"is not active, so there is no activation payload to fetch."
            )

        url = f"{base}/{version}/active.json"
        response = await authed_client.get(url)
        assert response.status_code == status.HTTP_200_OK, (
            f"Could not fetch active.json at {url} (status {response.status_code})"
        )
        return ProcessedConfiguration.from_dict(response.json())

    return _get


@pytest_asyncio.fixture
async def build_scenario_configuration(
    get_condition_id,
    get_condition_by_id,
    create_config,
    associate_codeset,
    add_custom_code,
    update_section_processing,
    activate_config,
    fetch_activation_payload,
    test_user_jurisdiction_id,
):
    """
    Author a scenario's configuration through the API, activate it, and read
    the activation payload back as a ProcessedConfiguration -- the same
    serialization lambda consumes. Replaces loading a committed JSON.

    Returns (processed_configuration, canonical_url). The canonical_url is
    derived from the seeded condition (and asserted to match the scenario's
    declared value) so the augmentation seed and the S3 path stay consistent
    with what production produces, rather than trusting a hand-declared value.
    """

    async def _build(scenario) -> tuple[ProcessedConfiguration, str]:
        condition_id = await get_condition_id(scenario.condition_name)
        config = await create_config(condition_id)
        config_id = config["id"]

        for name in scenario.associated_conditions:
            await associate_codeset(config_id, await get_condition_id(name))

        for cc in scenario.custom_codes:
            await add_custom_code(
                config_id,
                DbConfigurationCustomCode(
                    code=cc.code, system_key=cc.system, name=cc.name
                ),
            )

        for ov in scenario.section_overrides:
            await update_section_processing(
                config_id,
                current_code=ov.current_code,
                include=ov.include,
                narrative=ov.narrative,
                action=ov.action,
            )

        await activate_config(config_id)

        condition = await get_condition_by_id(condition_id)
        canonical_url = condition["canonical_url"]
        assert canonical_url == scenario.canonical_url, (
            f"[{scenario.name}] seeded canonical_url drifted from the value the "
            "snapshot was generated with."
        )

        # version is discovered from current.json so this stays correct even
        # when an earlier build in the same test already activated a config for
        # this condition (bumping it to version 2, etc)
        processed = await fetch_activation_payload(
            jurisdiction_id=test_user_jurisdiction_id,
            canonical_url=canonical_url,
        )
        return processed, canonical_url

    return _build

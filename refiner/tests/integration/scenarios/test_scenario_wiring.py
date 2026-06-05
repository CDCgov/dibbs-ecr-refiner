import json

import pytest

from app.core.models.types import XMLFiles
from app.services.terminology import ProcessedConfiguration

from ...fixtures.loader import load_fixture_str
from ...unit.conftest import normalize_xml
from .harness import make_fixed_run, refine_one

# NOTE:
# SCENARIO CONTEXT
# =============================================================================
# these constants describe the same scenario the lambda integration suite
# exercises through localstack (see tests/localstack/seed.py and
# tests/integration/test_lambda.py). reusing them confirms the harness
# reaches the same production code path lambda does, with S3/SQS replaced
# by disk reads

COVID_RSG_CODE: str = "840539006"
COVID_CANONICAL_URL: str = (
    "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
    "07221093-b8a1-4b1d-8678-259277bfba64"
)
JURISDICTION: str = "SDDH"
CONFIGURATION_VERSION: int = 1


# NOTE:
# FIXTURES
# =============================================================================


@pytest.fixture
def multi_condition_xml_files() -> XMLFiles:
    """
    The multi-condition-multi-covid eICR/RR pair.

    Same fixture seed_localstack uses; lambda's integration suite confirms
    it survives the full refinement + augmentation pipeline. Reusing it
    here keeps the smoke test on a known-good path.
    """

    return XMLFiles(
        eicr=load_fixture_str("eicr_v3_1_1/multi-condition-multi-covid-CDA_eICR.xml"),
        rr=load_fixture_str("eicr_v3_1_1/multi-condition-multi-covid-CDA_RR.xml"),
    )


@pytest.fixture
def covid_processed_configuration() -> ProcessedConfiguration:
    """
    The COVID configuration that lambda's seed_localstack writes to S3.

    Loaded here from the same committed fixture file rather than from S3,
    proving the disk -> ProcessedConfiguration path is equivalent to the
    S3 -> ProcessedConfiguration path lambda uses.
    """

    return ProcessedConfiguration.from_dict(
        json.loads(load_fixture_str("lambda/active.json"))
    )


# NOTE:
# SMOKE TESTS
# =============================================================================
# make sure the scenario wiring is in good working order


def test_harness_produces_a_refinement_result(
    multi_condition_xml_files: XMLFiles,
    covid_processed_configuration: ProcessedConfiguration,
) -> None:
    """
    The harness composes into a usable RefinementResult: augmentation mutates
    document identity, refinement actually removes content, and the refined
    documents are well-formed enough to normalize.

    Deliberately does NOT re-assert the trace's input-echo fields
    (configuration_version, canonical_url) or its success-path flags
    (configuration_resolved / skip_reason / error_detail / refinement_outcome):
    the former are values the caller passed in and the harness only carries
    back out, and the latter are implied by the refined XML existing at all --
    a skip or error path would leave refined_eicr empty and fail the Tier 3
    checks below. What remains is the set of derived properties that can break
    independently.
    """

    result = refine_one(
        xml_files=multi_condition_xml_files,
        processed_configuration=covid_processed_configuration,
        jurisdiction_code=JURISDICTION,
        rsg_code=COVID_RSG_CODE,
        canonical_url=COVID_CANONICAL_URL,
        configuration_version=CONFIGURATION_VERSION,
    )

    # augmentation mutated document identity: the augmented ids are populated
    # and differ from the originals (no-op augmentation would leave them equal)
    # - see DIBBs-eCR-Refiner-Augmentation-Guide.md
    assert result.augmented_eicr_result.augmented_doc_id
    assert result.augmented_eicr_result.original_doc_id
    assert result.augmented_rr_result.augmented_doc_id
    assert result.augmented_rr_result.original_doc_id
    assert (
        result.augmented_eicr_result.augmented_doc_id
        != result.augmented_eicr_result.original_doc_id
    )
    assert (
        result.augmented_rr_result.augmented_doc_id
        != result.augmented_rr_result.original_doc_id
    )

    # refinement actually did something: refining for COVID against a
    # multi-condition eICR must drop the non-COVID content. A bug that returned
    # the input unchanged would pass every other check here but fail this one
    assert result.trace.eicr_size_reduction_percentage is not None
    assert result.trace.eicr_size_reduction_percentage > 0

    # refined XML is populated and well-formed enough to normalize
    # (snapshot equality is asserted by the real scenarios; here we only
    # confirm the strings are usable)
    assert result.refined_eicr
    assert result.refined_rr
    assert normalize_xml(result.refined_eicr)
    assert normalize_xml(result.refined_rr)


def test_harness_output_is_deterministic_across_runs(
    multi_condition_xml_files: XMLFiles,
    covid_processed_configuration: ProcessedConfiguration,
) -> None:
    """
    Running the harness twice with the same inputs produces byte-identical output across all three assertion tiers.

    This is the load-bearing property for the whole scenarios suite. The
    fixed timestamp freezes the augmentation pipeline's only
    nondeterministic field, and every other identifier is a deterministic
    function of inputs the harness controls. If this assertion ever
    fails, snapshot-based scenarios cannot be relied on and the
    nondeterminism source must be found before regenerating any snapshot.
    """

    def run_once() -> dict[str, object]:
        result = refine_one(
            xml_files=multi_condition_xml_files,
            processed_configuration=covid_processed_configuration,
            jurisdiction_code=JURISDICTION,
            rsg_code=COVID_RSG_CODE,
            canonical_url=COVID_CANONICAL_URL,
            configuration_version=CONFIGURATION_VERSION,
        )
        return {
            "augmented_eicr_id": result.augmented_eicr_result.augmented_doc_id,
            "augmented_rr_id": result.augmented_rr_result.augmented_doc_id,
            "refined_eicr": result.refined_eicr,
            "refined_rr": result.refined_rr,
            "size_reduction": result.trace.eicr_size_reduction_percentage,
        }

    first = run_once()
    second = run_once()

    # compare fields individually so a failure points at the specific
    # axis of nondeterminism rather than collapsing into one big diff
    assert first["augmented_eicr_id"] == second["augmented_eicr_id"], (
        "augmented eICR id changed across runs - UUIDv5 derivation is no longer stable"
    )
    assert first["augmented_rr_id"] == second["augmented_rr_id"], (
        "augmented RR id changed across runs - UUIDv5 derivation is no longer stable"
    )
    assert first["refined_eicr"] == second["refined_eicr"], (
        "refined eICR XML changed across runs - "
        "nondeterminism somewhere in refine or augment"
    )
    assert first["refined_rr"] == second["refined_rr"], (
        "refined RR XML changed across runs - "
        "nondeterminism somewhere in refine or augment"
    )
    assert first["size_reduction"] == second["size_reduction"], (
        "size reduction percentage changed across runs"
    )


def test_harness_accepts_a_caller_supplied_run(
    multi_condition_xml_files: XMLFiles,
    covid_processed_configuration: ProcessedConfiguration,
) -> None:
    """
    A caller can build a single AugmentationRun and pass it to refine_one,
    matching production behavior where one run is shared across all
    per-condition refinements in a session (see lambda's run_refinement).

    The result must be byte-identical to the case where refine_one builds
    its own run with the same fixed timestamp.
    """

    shared_run = make_fixed_run(multi_condition_xml_files)

    result_explicit = refine_one(
        xml_files=multi_condition_xml_files,
        processed_configuration=covid_processed_configuration,
        jurisdiction_code=JURISDICTION,
        rsg_code=COVID_RSG_CODE,
        canonical_url=COVID_CANONICAL_URL,
        configuration_version=CONFIGURATION_VERSION,
        run=shared_run,
    )

    result_implicit = refine_one(
        xml_files=multi_condition_xml_files,
        processed_configuration=covid_processed_configuration,
        jurisdiction_code=JURISDICTION,
        rsg_code=COVID_RSG_CODE,
        canonical_url=COVID_CANONICAL_URL,
        configuration_version=CONFIGURATION_VERSION,
    )

    assert (
        result_explicit.augmented_eicr_result.augmented_doc_id
        == result_implicit.augmented_eicr_result.augmented_doc_id
    )
    assert (
        result_explicit.augmented_rr_result.augmented_doc_id
        == result_implicit.augmented_rr_result.augmented_doc_id
    )
    assert result_explicit.refined_eicr == result_implicit.refined_eicr
    assert result_explicit.refined_rr == result_implicit.refined_rr

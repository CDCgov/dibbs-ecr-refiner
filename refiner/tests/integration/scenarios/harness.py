from dataclasses import replace
from typing import Final

from app.core.models.types import XMLFiles
from app.services.ecr.augment import AugmentationRun
from app.services.pipeline import (
    RefinementContext,
    RefinementResult,
    create_augmentation_run_from_xml_files,
    refine_for_condition,
)
from app.services.terminology import ProcessedConfiguration
from tests.integration.conftest import test_user_jurisdiction_id

# NOTE:
# DETERMINISTIC TIMESTAMP
# =============================================================================
# format conforms to DTM.US.FIELDED (urn:oid:2.16.840.1.113883.10.20.22.5.4):
# strftime pattern is %Y%m%d%H%M%S%z:
# * this is the canonical augmentation time used by every scenario in this suite;
# changing it invalidates every committed snapshot because it propagates into:
#   - the augmented document's <effectiveTime>
#   - the augmentation author's <time>
#   - per-section provenance footnote IDs
#   - any element whose derivation reads it off the AugmentationRun
FIXED_AUGMENTATION_TIME: Final[str] = "20260101000000+0000"


# NOTE:
# HARNESS API
# =============================================================================


def make_fixed_run(xml_files: XMLFiles) -> AugmentationRun:
    """
    Build an AugmentationRun with the canonical fixed augmentation_time.

    Calls the real create_augmentation_run_from_xml_files (reading
    versionNumber and setId from the eICR exactly as production does),
    then dataclasses.replace's only the augmentation_time field.

    This is the minimum-surface freeze: the production construction logic
    still runs - including the ValueError guards for missing setId /
    versionNumber - and only the clock is replaced. If the construction
    logic later reads additional fields off the eICR, the harness picks
    them up without modification.

    Args:
        xml_files: The eICR/RR pair the AugmentationRun will be used for.
            Only the eICR is read.

    Returns:
        A frozen AugmentationRun whose augmentation_time is
        FIXED_AUGMENTATION_TIME and whose other fields come from the
        real production constructor.
    """

    real_run = create_augmentation_run_from_xml_files(xml_files)
    return replace(real_run, augmentation_time=FIXED_AUGMENTATION_TIME)


def refine_one(
    xml_files: XMLFiles,
    processed_configuration: ProcessedConfiguration,
    canonical_url: str,
    jurisdiction_code: str = test_user_jurisdiction_id,
    configuration_version: int | None = None,
    run: AugmentationRun | None = None,
) -> RefinementResult:
    """
    Run the production refinement path for a single (jurisdiction, condition) pair.

    Mirrors what lambda's run_refinement does for one condition, with S3
    amputated: the caller supplies the already-resolved
    ProcessedConfiguration (loaded from a committed JSON, not from S3)
    and the canonical_url that seeds the deterministic augmented
    identifiers.

    If `run` is None, a fixed-time run is built from `xml_files`. Tests
    that exercise multiple conditions on a single input pair should
    construct one run via make_fixed_run() and pass it to every refine_one
    call, matching production behavior where a single AugmentationRun is
    shared across all per-condition refinements in a session.

    NOTE: Augmentation is seeded by the jurisdiction the config was activated
    under (the live test infra: SDDH), NOT the RR's reportable-to jurisdiction.
    The fixture RR may be reportable elsewhere; that's intentionally not
    consulted here--it isn't a refinement input.

    Args:
        xml_files: The eICR/RR pair to refine.
        processed_configuration: The fully resolved configuration.
        jurisdiction_code: The jurisdiction the configuration applies to.
        rsg_code: The reportable SNOMED code being refined for.
        canonical_url: The TES condition grouper's canonical_url. Its
            trailing UUID seeds the deterministic augmented identifiers.
        configuration_version: The configuration version. Recorded on
            the trace for assertion; does not affect refinement.
        run: An optional pre-built AugmentationRun. If None, one is
            built with the fixed timestamp.

    Returns:
        The RefinementResult produced by the shared pipeline.
    """

    if run is None:
        run = make_fixed_run(xml_files)

    context = RefinementContext(
        jurisdiction_id=jurisdiction_code,
        canonical_url=canonical_url,
        configuration_version=configuration_version,
    )

    return refine_for_condition(
        xml_files=xml_files,
        processed_configuration=processed_configuration,
        context=context,
        run=run,
    )

import re
import unicodedata
from dataclasses import dataclass

from app.core.models.types import XMLFiles
from app.db.conditions.model import (
    ConditionMappingPayload,
    ConditionMapValue,
    DbCondition,
)
from app.services.ecr.model import RefinedDocument
from app.services.ecr.refine import get_file_size_in_bytes


def get_computed_condition_name(condition_name: str) -> str:
    """
    Given a condition name returns the computed name.

    For example:
    - `COVID-19` becomes `COVID19`
    - `Drowning and Submersion` becomes `DrowningandSubmersion`

    Args:
        condition_name (str): The name of the condition

    Returns:
        str: The computed condition name
    """
    # !!NOTE!!
    # TES versions 1-3 have the computed name `Tickborne_relapsing_feverTBRF` and
    # version 4 has the computed name `Tickborne_relapsing_fever_TBRF` which is probably a bug

    normalized = unicodedata.normalize("NFKD", condition_name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"\s+", "", normalized.strip())
    normalized = re.sub(r"[^A-Za-z0-9_]", "", normalized)
    return normalized


def create_condition_mapping_payload(
    conditions: list[DbCondition],
) -> ConditionMappingPayload:
    """
    Maps RSG codes to all possible matching CGs.

    Args:
        conditions (list[DbCondition]): A list of condition information

    Returns:
        ConditionMappingPayload: Typed dictionary containing condition mapping info
    """
    payload = ConditionMappingPayload()
    for condition in conditions:
        name = condition.display_name
        tes_version = condition.version

        for rsg in condition.child_rsg_snomed_codes:
            if not rsg or not rsg.strip():
                continue

            rsg = rsg.strip()
            value = ConditionMapValue(
                canonical_url=condition.canonical_url,
                name=get_computed_condition_name(name),
                tes_version=tes_version,
            )

            exists = payload.mappings.get(rsg)
            if exists is not None and exists != value:
                raise ValueError(
                    f"Collision for RSG code {rsg}: "
                    f"{exists.canonical_url} vs {condition.canonical_url}"
                )

            payload.mappings[rsg] = value

    return payload


@dataclass
class ConditionRefinementForDisplay:
    """
    Packaged strings for the frontend, conditionally packaged based on the decision to render the diff.
    """

    render_diff: bool
    refined_eicr: str
    original_eicr: str


def filter_refined_files_by_diff_rendering(
    original_xml_files: XMLFiles, refined_document: RefinedDocument
) -> ConditionRefinementForDisplay:
    """
    Function to decide whether to filter files being sent to the frontend based on rendering size.

    Args:
        original_xml_files: Inputted files.
        refined_document: Refined documents to potentially ship to potentially render in the diff

    Returns:
        FilesFor - with values being the strings to send to the frontend.

    """
    from app.api.validation.file_validation import (
        DIFF_RENDERING_MAX_BYTES,
        format_xml_document_for_display_or_raise,
    )

    render_diff = (
        get_file_size_in_bytes(original_xml_files.eicr) < DIFF_RENDERING_MAX_BYTES  # noqa: F821
    )

    original_eicr = ""
    refined_eicr = ""

    if render_diff:
        original_eicr = format_xml_document_for_display_or_raise(
            original_xml_files.eicr
        )
        refined_eicr = format_xml_document_for_display_or_raise(
            refined_document.refined_eicr
        )

    return ConditionRefinementForDisplay(
        render_diff=render_diff,
        refined_eicr=refined_eicr,
        original_eicr=original_eicr,
    )

from dataclasses import dataclass

from app.api.validation.file_validation import (
    DIFF_RENDERING_MAX_BYTES,
    format_xml_document_for_display_or_raise,
)
from app.core.models.types import XMLFiles
from app.services.ecr.model import RefinedDocument
from app.services.ecr.refine import get_file_size_in_bytes


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

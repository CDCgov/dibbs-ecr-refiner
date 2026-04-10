"""
Refiner policy constants.

This module holds constants that represent *policy decisions* made by the
refiner — things that are not derived from the eICR Implementation Guide
itself, but from how the refiner has chosen to behave.

The distinction matters: `specification/` models what the IGs say, and is
IG-traceable. This module models what the refiner does, and is
refiner-traceable. A reader wondering "why does the refiner skip this
section?" should find the answer here, not in the specification, because
the IG doesn't tell us to skip it — we decided to.
"""

from typing import Final

# NOTE:
# SECTIONS ALWAYS RETAINED REGARDLESS OF JURISDICTION CONFIGURATION
# =============================================================================
# These sections are preserved intact in every refined document, even if a
# jurisdiction has not configured them. They exist outside the normal
# refinement workflow because their content is either public-health
# infrastructure (outbreak information) or downstream routing metadata
# (reportability response content) that jurisdictions expect to see
# untouched in the refined output.
#
# In the future we may decide to implement new ways to handle these sections
# but for now skipping them is easier and produces valid (Schematron-valid)
# output.

SECTION_PROCESSING_SKIP: Final[set[str]] = {
    "83910-0",  # emergency outbreak information section
    "88085-6",  # reportability response information section
}

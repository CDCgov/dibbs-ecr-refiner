import re
from typing import Final

# NOTE:
# REFINER ID NAMESPACE
# =============================================================================
# every xs:ID the refiner mints — the per-section provenance footnote
# (footnote.py) and the reconstructed detail rows (reconstruction.py) — shares
# one namespace: `ecr-refiner-{loinc}-{run-digits}[...]`. owning the prefix and
# the run-digit extraction here keeps the two ID schemes structurally
# consistent, so a consumer can tie a footnote and the rows of the same run
# together by their shared stamp
#
# xs:ID cannot start with a digit or hyphen, so the `ecr-refiner-` prefix is
# load-bearing: it guarantees the result satisfies the XML Name production

REFINER_ID_PREFIX: Final[str] = "ecr-refiner-"


def run_id_digits(augmentation_timestamp: str) -> str:
    """
    Extract the leading digit run from the augmentation timestamp.

    The augmentation author's <time> is HL7 V3 ``YYYYMMDDHHMMSS±ZZZZ``;
    keeping the leading run of digits drops the timezone offset (the ``+``
    and offset digits are unwanted in an ID), giving every ID minted in a
    run the same stamp.

    Args:
        augmentation_timestamp: The refinement run's HL7 V3 time value.

    Returns:
        The leading digit run, or "" when the input has no leading digits.
    """

    match = re.match(r"^\d+", augmentation_timestamp)
    return match.group(0) if match else ""


# an entry-side <text> wrapping only a reconstruction reference. pretty-printing
# the whole document indents it into mixed content (<text>\n  <reference/>\n</text>),
# which adds stray character data around the <reference> — the form Boone (The CDA
# Book, ch. 6) flags as incorrect for a mixed-content reference. built from the
# prefix above so it stays scoped to refiner-minted ids (source narrative
# references are left untouched) and cannot drift if the prefix changes
_RECONSTRUCTION_REFERENCE: Final = re.compile(
    rf'<text>\s*(<reference value="#{re.escape(REFINER_ID_PREFIX)}[^"]*"\s*/>)\s*</text>'
)


def compact_reconstruction_references(text: str) -> str:
    """
    Collapse whitespace around reconstruction entry→narrative references.

    Pretty-printing the document indents each minted ``<text><reference/></text>``
    pointer into mixed content with stray whitespace nodes around the
    ``<reference>``. CDA's reference is a mixed-content element that must not
    carry surrounding whitespace (Boone, The CDA Book, ch. 6), so this restores
    the compact ``<text><reference value="#..."/></text>`` form. Scoped to the
    refiner-minted ids; author-attested narrative references are not touched.

    Args:
        text: A serialized (pretty-printed) XML document.

    Returns:
        The document with reconstruction references in compact form.
    """

    return _RECONSTRUCTION_REFERENCE.sub(r"<text>\1</text>", text)

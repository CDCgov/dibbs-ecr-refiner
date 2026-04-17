from collections import defaultdict

from lxml.etree import _Element

from ..model import (
    HL7_NS,
    EICRSpecification,
    EicrVersion,
    SectionSpecification,
)
from .catalog import _SECTION_CATALOG
from .constants import EICR_VERSION_MAP
from .versions import _VERSION_SECTIONS, _VERSION_TRIGGERS

# NOTE:
# VERSION DETECTION
# =============================================================================


def detect_eicr_version(xml_root: _Element) -> EicrVersion:
    """
    Inspect an eICR document's templateId to determine its version.

    Looks for the eICR Public Health Case Report templateId
    (root="2.16.840.1.113883.10.20.15.2") and reads its ``@extension``
    attribute, which carries a date-formatted version marker
    (e.g., "2016-12-01" -> "1.1", "2022-05-01" -> "3.1.1").

    Defaults to "1.1" if the templateId is missing, the extension is
    missing, or the extension doesn't match a known version. The
    fallback is conservative: 1.1 has the smallest set of sections,
    so misclassifying a 3.x document as 1.1 results in fewer sections
    being processed but won't apply 3.x-only rules to a 1.1 document.

    Args:
        xml_root: The root element of an eICR document
            (the <ClinicalDocument>).

    Returns:
        The detected EicrVersion, or "1.1" as a fallback.
    """

    template_id = xml_root.find(
        'hl7:templateId[@root="2.16.840.1.113883.10.20.15.2"]',
        namespaces=HL7_NS,
    )

    if template_id is not None:
        version_date = template_id.get("extension")
        if version_date and version_date in EICR_VERSION_MAP:
            return EICR_VERSION_MAP[version_date]

    return "1.1"


# NOTE:
# SPECIFICATION ASSEMBLY
# =============================================================================


def load_spec(version: EicrVersion) -> EICRSpecification:
    """
    Assemble the specification for a specific eICR version.

    Merges the stable section catalog with version-specific trigger
    codes to produce a fully-resolved ``EICRSpecification``. The
    catalog provides invariant C-CDA structural data (templateIds,
    display names, entry match rules); the version manifest provides
    which sections exist in this version and which trigger code OIDs
    apply per section.

    For each section in the version's section list:

      1. Look up the catalog entry by LOINC code.
      2. If the version has trigger codes for that section, build a
         new `SectionSpecification` with the trigger codes added.
         `SectionSpecification` is frozen, so this is a rebuild
         rather than a mutation.
      3. If the version has no trigger codes for that section, use
         the catalog entry as-is.

    If the requested version is not in `_VERSION_SECTIONS` (e.g.,
    a future version not yet supported), falls back to "1.1" — the
    same conservative default as `detect_eicr_version`.

    Args:
        version: The eICR version to load.

    Returns:
        A fully-resolved EICRSpecification with all sections present
        in the version, each with their version-appropriate trigger
        codes overlaid.
    """

    # resolve version — fall back to 1.1 for unknown versions
    if version not in _VERSION_SECTIONS:
        version = "1.1"

    section_codes = _VERSION_SECTIONS[version]
    trigger_map = _VERSION_TRIGGERS.get(version, {})

    sections: dict[str, SectionSpecification] = {}

    for loinc_code in section_codes:
        catalog_entry = _SECTION_CATALOG.get(loinc_code)
        if catalog_entry is None:
            continue  # section not in catalog — skip gracefully

        # overlay version-specific trigger codes onto the catalog entry
        version_triggers = trigger_map.get(loinc_code, [])

        if version_triggers:
            # SectionSpecification is frozen, so rebuild rather than mutate
            spec = SectionSpecification(
                loinc_code=catalog_entry.loinc_code,
                display_name=catalog_entry.display_name,
                template_id=catalog_entry.template_id,
                trigger_codes=version_triggers,
                entry_match_rules=catalog_entry.entry_match_rules,
            )
        else:
            # no trigger codes for this section in this version — use catalog as-is
            spec = catalog_entry

        sections[loinc_code] = spec

    return EICRSpecification(version=version, sections=sections)


# NOTE:
# SECTION-VERSION MAPPING
# =============================================================================


def get_section_version_map() -> dict[str, list[str]]:
    """
    Build a section LOINC -> sorted list of versions mapping.

    Inverts `_VERSION_SECTIONS` so that the resulting dict is keyed
    by section LOINC and each value is the sorted list of eICR versions
    that include that section. Used by the configuration service to
    tag sections with their version availability when presenting them
    to jurisdiction reviewers in the application UI.

    Returns:
        Dictionary mapping each section LOINC code to a sorted list
        of EicrVersion strings that include the section.
    """

    loinc_version_map: dict[str, set[str]] = defaultdict(set)
    for version, section_codes in _VERSION_SECTIONS.items():
        for loinc in section_codes:
            loinc_version_map[loinc].add(version)

    return {k: sorted(v) for k, v in loinc_version_map.items()}

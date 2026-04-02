from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from uuid import uuid4

from lxml import etree
from lxml.etree import _Element

from .model import HL7_NAMESPACE, HL7_NS

# NOTE:
# CONSTANTS
# =============================================================================

# oids and code system identifiers from the augmentation ig
ECR_DATA_AUG_CODE_SYSTEM: Final[str] = "2.16.840.1.113883.10.20.15.2.7.1"
ECR_DATA_AUG_CODE_SYSTEM_NAME: Final[str] = "eCRDataAugmentation"

# template identifiers
AUG_HEADER_TEMPLATE_ROOT: Final[str] = "2.16.840.1.113883.10.20.15.2.1.3"
AUG_HEADER_TEMPLATE_EXT: Final[str] = "2025-11-01"

# refiner tool identity -> from data augmentation tool value set
REFINER_TOOL_CODE: Final[str] = "ecr-refinement"
REFINER_TOOL_DISPLAY: Final[str] = "eCR Refiner"

# document source label -> from data augmentation document source value set
ORIGINAL_DOCUMENT_SOURCE: Final[str] = "original-document"


# NOTE:
# CONTEXT
# =============================================================================


@dataclass(frozen=True)
class AugmentationContext:
    """
    Pre-computed values needed to stamp a refined document.

    Created once per document by the pipeline before augmentation begins.
    Keeps the XML-manipulation functions pure — no UUID generation or
    clock reads happen inside them.

    Attributes:
        new_doc_id: UUID for the augmented document's <id>.
        new_set_id: UUID for the augmented document's <setId>.
        augmentation_time: HL7 V3 formatted timestamp with timezone
            offset (e.g., "20250108124500-0500"). Conforms to
            DTM.US.FIELDED (urn:oid:2.16.840.1.113883.10.20.22.5.4).
        tool_code: Code from the Data Augmentation Tool value set
            (Table 2). Defaults to "ecr-refinement".
        tool_display: Human-readable display name for the tool.
            Defaults to "eCR Refiner".
    """

    new_doc_id: str
    new_set_id: str
    augmentation_time: str
    tool_code: str = REFINER_TOOL_CODE
    tool_display: str = REFINER_TOOL_DISPLAY


def create_augmentation_context(
    tool_code: str = REFINER_TOOL_CODE,
    tool_display: str = REFINER_TOOL_DISPLAY,
    augmentation_time: str | None = None,
) -> AugmentationContext:
    """
    Factory that generates UUIDs and captures a timestamp.

    The timestamp includes a UTC offset per DTM.US.FIELDED requirements
    (eICR IG Vol. 2 STU3.1.1, author/time conformance).

    Args:
        tool_code: Code from the Data Augmentation Tool value set.
        tool_display: Human-readable display name for the tool.
        augmentation_time: Optional pre-formatted HL7 timestamp. When
            provided, this timestamp is used instead of capturing the
            current time. Useful when multiple documents should share
            the same augmentation timestamp (e.g., eICR/RR pairs).

    Returns:
        A fully populated AugmentationContext ready for use.
    """

    if augmentation_time is None:
        now = datetime.now(UTC).astimezone()
        augmentation_time = now.strftime("%Y%m%d%H%M%S%z")

    return AugmentationContext(
        new_doc_id=str(uuid4()),
        new_set_id=str(uuid4()),
        augmentation_time=augmentation_time,
        tool_code=tool_code,
        tool_display=tool_display,
    )


# NOTE:
# CAPTURED IDENTITY (for relatedDocument lineage)
# =============================================================================


@dataclass(frozen=True)
class _OriginalIdentity:
    """
    The document-identity elements captured from the input document before they are replaced.

    Used to populate the relatedDocument/parentDocument block.

    set_id_element and version_number_element may be None — these are
    optional in CDA R2 and many real-world eICRs (especially 1.1-era
    documents) omit them.
    """

    id_element: _Element
    set_id_element: _Element | None
    version_number_element: _Element | None
    existing_xfrm_parent_doc_ids: list[_Element]


# NOTE:
# PUBLIC API — EICR
# =============================================================================


@dataclass
class AugmentedResult:
    """
    This is the result of eICR/RR augmentation.
    """

    original_doc_id: str
    augmented_doc_id: str


def augment_eicr(
    eicr_root: _Element,
    context: AugmentationContext,
) -> AugmentedResult:
    """
    Apply all document-level augmentation to a refined eICR.

    Mutates `eicr_root` in place.

    Implements the eICR Data Augmentation Header template constraints
    (CONF:5573-1 through CONF:5573-39).

    The steps execute in a specific order that respects the CDA R2
    schema's required element sequence within <ClinicalDocument>:
    templateId → id → effectiveTime → setId → versionNumber → author
    → relatedDocument.

    Args:
        eicr_root: The parsed root <ClinicalDocument> element. Must
            be namespace-qualified (urn:hl7-org:v3).
        context: Pre-computed augmentation values (UUIDs, timestamp, tool
            identity).
    """

    # STEP 1:
    # snapshot the current identity before we overwrite anything
    original = _capture_original_identity(eicr_root)

    # STEP 2:
    # add augmentation templateId (CONF:5573-18/19/20)
    _add_augmentation_template_id(eicr_root)

    # STEP 3:
    # replace document id (new uuid, assigningAuthorityName = tool code)
    augmented_result = _replace_document_id(eicr_root, context)

    # STEP 4:
    # replace effectiveTime with augmentation timestamp
    _replace_effective_time(eicr_root, context)

    # STEP 5:
    # replace setId with new uuid
    _replace_set_id(eicr_root, context)

    # STEP 6:
    # reset versionNumber to 1
    _replace_version_number(eicr_root)

    # STEP 7:
    # add header-level augmentation author (CONF:5573-1 through 5573-17)
    _add_augmentation_author(eicr_root, context)

    # STEP 8:
    # add relatedDocument with XFRM lineage (CONF:5573-12 through 5573-23)
    _add_related_document(eicr_root, original)

    return augmented_result


# NOTE:
# PUBLIC API — RR
# =============================================================================


def augment_rr(
    rr_root: _Element,
    context: AugmentationContext,
) -> AugmentedResult:
    """
    Apply document-level augmentation to a refined RR.

    Mutates `rr_root` in place.

    The augmentation IG does not define RR-specific templates, so this
    applies the same document-identity and provenance patterns used for
    the eICR, adapted for the RR's simpler header:

    - NO augmentation templateId (that template conforms to eICR V5,
      not the RR)
    - setId and versionNumber are only replaced if the original had
      them. RRs are typically one-shot response documents without
      versioning, so these elements are usually absent. We don't
      fabricate them.

    Args:
        rr_root: The parsed root <ClinicalDocument> element of the RR.
        context: Pre-computed augmentation values.
    """

    # STEP 1:
    # snapshot the current identity
    original = _capture_original_identity(rr_root)

    # STEP 2:
    # NO augmentation templateId for RR

    # STEP 3:
    # replace document id
    augmented_result = _replace_document_id(rr_root, context)

    # STEP 4:
    # replace effectiveTime
    _replace_effective_time(rr_root, context)

    # STEP 5:
    # replace setId only if original had one
    if original.set_id_element is not None:
        _replace_set_id(rr_root, context)

    # STEP 6:
    # reset versionNumber only if original had one
    if original.version_number_element is not None:
        _replace_version_number(rr_root)

    # STEP 7:
    # add header-level augmentation author
    _add_augmentation_author(rr_root, context)

    # STEP 8:
    # add relatedDocument with XFRM lineage
    _add_related_document(rr_root, original)

    return augmented_result


# NOTE:
# PRIVATE HELPERS — IDENTITY CAPTURE
# =============================================================================


def _capture_original_identity(doc_root: _Element) -> _OriginalIdentity:
    """
    Snapshot the input document's identity elements before replacement.

    Also inspects whether the input is itself an augmented document
    (has a relatedDocument[@typeCode='XFRM']) and, if so, captures the
    existing parentDocument/id chain for cumulative lineage per
    CONF:5573-14 ("cumulative list of all prior document ids").

    Works for both eICR and RR documents — both are CDA
    ClinicalDocuments with the same header structure.

    Note: <setId> and <versionNumber> are optional in CDA R2 and may
    be absent in real-world eICRs. They are captured as None when missing.
    """

    doc_id = _find_required(doc_root, "hl7:id")

    # setId and versionNumber are optional in CDA R2
    set_id = doc_root.find("hl7:setId", HL7_NS)
    version = doc_root.find("hl7:versionNumber", HL7_NS)

    # check for an existing XFRM relatedDocument (input was already augmented)
    existing_parent_ids: list[_Element] = []
    existing_xfrm = doc_root.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    if existing_xfrm is not None:
        parent_doc = existing_xfrm.find("hl7:parentDocument", HL7_NS)
        if parent_doc is not None:
            existing_parent_ids = parent_doc.findall("hl7:id", HL7_NS)

    # deep-copy so mutations to the tree don't affect our snapshot
    return _OriginalIdentity(
        id_element=deepcopy(doc_id),
        set_id_element=deepcopy(set_id) if set_id is not None else None,
        version_number_element=deepcopy(version) if version is not None else None,
        existing_xfrm_parent_doc_ids=[deepcopy(e) for e in existing_parent_ids],
    )


# NOTE:
# PRIVATE HELPERS — ELEMENT REPLACEMENT
# =============================================================================


def _add_augmentation_template_id(doc_root: _Element) -> None:
    """
    Insert the eICR Data Augmentation Header templateId (CONF:5573-18/19/20).

    Placed immediately before the document <id>, after any existing
    templateId elements, to maintain CDA schema element ordering.
    """

    new_template_id = _make_element(
        "templateId",
        root=AUG_HEADER_TEMPLATE_ROOT,
        extension=AUG_HEADER_TEMPLATE_EXT,
    )

    # insert just before <id> — all templateIds precede <id> in the CDA schema
    doc_id = _find_required(doc_root, "hl7:id")
    doc_id.addprevious(new_template_id)


def _replace_document_id(
    doc_root: _Element, context: AugmentationContext
) -> AugmentedResult:
    """
    Replace the document <id> with a new UUID and assigningAuthorityName.

    The assigningAuthorityName is set to the tool code ("ecr-refinement")
    per the Data Augmentation Document Source value set (Table 3).
    """

    old_id = _find_required(doc_root, "hl7:id")

    new_id = _make_element(
        "id",
        root=context.new_doc_id,
        assigningAuthorityName=context.tool_code,
    )

    _replace_preserving_tail(doc_root, old_id, new_id)

    return AugmentedResult(
        original_doc_id=_toStr(old_id, "root"),
        augmented_doc_id=_toStr(new_id, "root"),
    )


def _replace_effective_time(doc_root: _Element, context: AugmentationContext) -> None:
    """
    Replace the document <effectiveTime> with the augmentation timestamp.
    """

    old_eff = _find_required(doc_root, "hl7:effectiveTime")
    new_eff = _make_element("effectiveTime", value=context.augmentation_time)
    _replace_preserving_tail(doc_root, old_eff, new_eff)


def _replace_set_id(doc_root: _Element, context: AugmentationContext) -> None:
    """
    Replace or insert the document <setId> with a new UUID.

    If <setId> doesn't exist (optional in CDA R2), inserts one in the
    correct schema position: after <languageCode> or <confidentialityCode>,
    before <versionNumber> or <recordTarget>.
    """

    new_set_id = _make_element("setId", root=context.new_set_id)
    old_set_id = doc_root.find("hl7:setId", HL7_NS)

    if old_set_id is not None:
        _replace_preserving_tail(doc_root, old_set_id, new_set_id)
    else:
        # insert in correct CDA schema position
        # setId comes after languageCode/confidentialityCode, before
        # versionNumber/recordTarget
        _insert_before_first_found(
            doc_root,
            new_set_id,
            ["hl7:versionNumber", "hl7:recordTarget"],
        )


def _replace_version_number(doc_root: _Element) -> None:
    """
    Replace or insert <versionNumber>, set to 1.

    Per the augmentation IG examples, each augmentation produces a new
    document (new id, new setId) with versionNumber starting at 1.

    If <versionNumber> doesn't exist (optional in CDA R2), inserts one
    in the correct schema position: after <setId>, before <recordTarget>.
    """

    new_version = _make_element("versionNumber", value="1")
    old_version = doc_root.find("hl7:versionNumber", HL7_NS)

    if old_version is not None:
        _replace_preserving_tail(doc_root, old_version, new_version)
    else:
        _insert_before_first_found(
            doc_root,
            new_version,
            ["hl7:recordTarget"],
        )


# NOTE:
# PRIVATE HELPERS — AUTHOR
# =============================================================================


def _add_augmentation_author(doc_root: _Element, context: AugmentationContext) -> None:
    """
    Add the header-level augmentation author (CONF:5573-1 through 5573-17).

    The author is appended after any existing <author> elements. CDA R2
    allows multiple authors on a document and the schema requires they
    appear in sequence after <recordTarget> but before <custodian>.

    Under the current (pre-March-2026-update) spec:
        - functionCode carries the tool identity from the Data Augmentation
          Tool value set (Table 2): code="ecr-refinement"
        - softwareName/@displayName is set to "Data Augmentation Tool"
          per CONF:5573-17

    Under the March 2026 update:
        - functionCode is removed from the header-level author
        - softwareName gets a value set binding to the Data Augmentation
          Tool value set, carrying the tool identity as coded attributes
        To adopt the update, remove the functionCode block and add
        @code/@codeSystem to the softwareName element.
    """

    ns = HL7_NAMESPACE

    author = _make_element("author")

    # functionCode — Data Augmentation Tool value set (CONF:5573-2)
    # TODO: remove this block when adopting the march 2026 update
    function_code = etree.SubElement(author, f"{{{ns}}}functionCode")
    function_code.set("code", context.tool_code)
    function_code.set("codeSystem", ECR_DATA_AUG_CODE_SYSTEM)
    function_code.set("codeSystemName", ECR_DATA_AUG_CODE_SYSTEM_NAME)

    # time -> augmentation operation timestamp (CONF:5573-3)
    time_el = etree.SubElement(author, f"{{{ns}}}time")
    time_el.set("value", context.augmentation_time)

    # assignedAuthor (CONF:5573-4)
    assigned_author = etree.SubElement(author, f"{{{ns}}}assignedAuthor")

    # id nullFlavor="NA" (CONF:5573-5/6)
    _add_null_flavor_child(assigned_author, "id")

    # addr nullFlavor="NA" (CONF:5573-7/9)
    _add_null_flavor_child(assigned_author, "addr")

    # telecom nullFlavor="NA" (CONF:5573-8/10)
    _add_null_flavor_child(assigned_author, "telecom")

    # assignedAuthoringDevice (CONF:5573-11)
    device = etree.SubElement(assigned_author, f"{{{ns}}}assignedAuthoringDevice")

    # softwareName (CONF:5573-17)
    software_name = etree.SubElement(device, f"{{{ns}}}softwareName")
    software_name.set("displayName", "Data Augmentation Tool")

    # insert after the last existing <author> and before <custodian>
    _insert_author(doc_root, author)


def _insert_author(doc_root: _Element, new_author: _Element) -> None:
    """
    Insert an author element in the correct CDA schema position.

    CDA R2 element order within ClinicalDocument is:
        ... → recordTarget → author → ... → custodian → ...

    We insert after the last existing <author>. If none exist (unusual
    but theoretically possible), we insert before <custodian>.
    """

    existing_authors = doc_root.findall("hl7:author", HL7_NS)

    if existing_authors:
        last_author = existing_authors[-1]
        last_author.addnext(new_author)
    else:
        # fall back to inserting before custodian
        custodian = doc_root.find("hl7:custodian", HL7_NS)
        if custodian is not None:
            custodian.addprevious(new_author)
        else:
            # last resort -> just append (not ideal but doesn't lose data)
            doc_root.append(new_author)


# NOTE:
# PRIVATE HELPERS — RELATED DOCUMENT
# =============================================================================


def _add_related_document(
    doc_root: _Element,
    original: _OriginalIdentity,
) -> None:
    """
    Add (or replace) the relatedDocument[@typeCode='XFRM'] block.

    Per CONF:5573-12 through 5573-23, the parentDocument must contain
    a cumulative list of all prior document IDs with their
    assigningAuthorityName drawn from the Data Augmentation Document
    Source value set (Table 3).

    Chaining logic:
        - If the input was an original document (no existing XFRM):
            parentDocument gets one <id> with
            assigningAuthorityName="original-document"
        - If the input was already augmented (has existing XFRM):
            parentDocument gets all prior IDs carried forward, plus the
            input document's own <id> with its assigningAuthorityName
    """

    ns = HL7_NAMESPACE

    # remove any existing XFRM relatedDocument — we'll rebuild it
    existing_xfrm = doc_root.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    if existing_xfrm is not None:
        doc_root.remove(existing_xfrm)

    # build the new relatedDocument
    related_doc = _make_element("relatedDocument", typeCode="XFRM")
    parent_doc = etree.SubElement(related_doc, f"{{{ns}}}parentDocument")

    # build the cumulative ID chain
    if original.existing_xfrm_parent_doc_ids:
        # input was already augmented — carry forward all prior ids
        for prior_id in original.existing_xfrm_parent_doc_ids:
            parent_doc.append(prior_id)

        # add the input document's own id (the one we just replaced)
        input_id = original.id_element
        # ensure it has an assigningAuthorityName
        if input_id.get("assigningAuthorityName") is None:
            input_id.set("assigningAuthorityName", ORIGINAL_DOCUMENT_SOURCE)
        parent_doc.append(input_id)
    else:
        # input was an original document — single id entry
        original_id = original.id_element
        if original_id.get("assigningAuthorityName") is None:
            original_id.set("assigningAuthorityName", ORIGINAL_DOCUMENT_SOURCE)
        parent_doc.append(original_id)

    # setId and versionNumber from the input document (CONF:5573-15/16)
    # only include if they were present in the original
    if original.set_id_element is not None:
        parent_doc.append(original.set_id_element)
    if original.version_number_element is not None:
        parent_doc.append(original.version_number_element)

    # insert in the correct CDA position -> relatedDocument comes after
    # -> custodian and before -> componentOf
    _insert_related_document(doc_root, related_doc)


def _insert_related_document(doc_root: _Element, related_doc: _Element) -> None:
    """
    Insert relatedDocument in the correct CDA schema position.

    CDA R2 ordering: ... → custodian → ... → relatedDocument → ... →
    componentOf → component.

    We insert before <componentOf> if it exists, otherwise before
    <component>.
    """

    component_of = doc_root.find("hl7:componentOf", HL7_NS)
    if component_of is not None:
        component_of.addprevious(related_doc)
        return

    component = doc_root.find("hl7:component", HL7_NS)
    if component is not None:
        component.addprevious(related_doc)
        return

    # last resort
    doc_root.append(related_doc)


# NOTE:
# XML UTILITIES
# =============================================================================


def _make_element(local_name: str, **attribs: str) -> _Element:
    """
    Create a namespace-qualified CDA element with optional attributes.

    All elements are created in the urn:hl7-org:v3 namespace so they
    inherit the document's default namespace declaration and serialise
    without a prefix.
    """

    element = etree.Element(f"{{{HL7_NAMESPACE}}}{local_name}")
    for key, value in attribs.items():
        element.set(key, value)
    return element


def _add_null_flavor_child(parent: _Element, local_name: str) -> _Element:
    """
    Add a child element with nullFlavor="NA" (CONF:5573-6/9/10/47/48/49).
    """

    child = etree.SubElement(parent, f"{{{HL7_NAMESPACE}}}{local_name}")
    child.set("nullFlavor", "NA")
    return child


def _find_required(doc_root: _Element, xpath: str) -> _Element:
    """
    Find a single required element or raise.

    Args:
        doc_root: The root element to search within.
        xpath: An XPath expression using the hl7 namespace prefix.

    Returns:
        The found element.

    Raises:
        ValueError: If the element is not found.
    """

    result = doc_root.find(xpath, HL7_NS)
    if result is None:
        raise ValueError(f"Required element not found in document: {xpath}")
    return result


def _insert_before_first_found(
    parent: _Element,
    new_element: _Element,
    candidate_xpaths: list[str],
) -> None:
    """
    Insert an element before the first existing sibling found by XPath.

    Tries each XPath in order. If a match is found, inserts ``new_element``
    immediately before it. If no candidates are found, appends to the parent.

    Used to insert optional CDA header elements (setId, versionNumber)
    into the correct schema position when they weren't present in the
    original document.
    """

    for xpath in candidate_xpaths:
        target = parent.find(xpath, HL7_NS)
        if target is not None:
            target.addprevious(new_element)
            return

    parent.append(new_element)


def _replace_preserving_tail(parent: _Element, old: _Element, new: _Element) -> None:
    """
    Replace an element while preserving its tail text (whitespace).

    lxml stores inter-element whitespace in the ``tail`` property of
    the preceding element. Without this, pretty-printing breaks.
    """

    new.tail = old.tail
    parent.replace(old, new)


def _toStr(node: _Element, key: str) -> str:
    value = node.get(key)
    if not value:
        raise ValueError("Cannot convert XML to string. No value found at key {key}.")
    return value

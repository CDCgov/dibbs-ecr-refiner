import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import urlparse

from lxml import etree
from lxml.etree import _Element

from .model import HL7_NAMESPACE, HL7_NS

# NOTE:
# CONSTANTS
# =============================================================================

# oids and code system identifiers from the augmentation ig
ECR_DATA_AUG_CODE_SYSTEM: Final[str] = "2.16.840.1.113883.10.20.15.2.7.1"
ECR_DATA_AUG_CODE_SYSTEM_NAME: Final[str] = "eCRDataAugmentation"

# template identifiers — eICR Data Augmentation Header
EICR_AUG_HEADER_TEMPLATE_ROOT: Final[str] = "2.16.840.1.113883.10.20.15.2.1.3"
EICR_AUG_HEADER_TEMPLATE_EXT: Final[str] = "2025-11-01"

# template identifiers — RR Data Augmentation Header (added in v4 — see
# Vol 1 §2 and Vol 2 §1.2)
RR_AUG_HEADER_TEMPLATE_ROOT: Final[str] = "2.16.840.1.113883.10.20.15.2.1.4"
RR_AUG_HEADER_TEMPLATE_EXT: Final[str] = "2026-04-01"

# refiner tool identity -> from data augmentation tool value set (Vol 2 Table 2)
# we need them to change it from "ecr-refinement" -> "ecr-refiner"
REFINER_TOOL_CODE: Final[str] = "ecr-refiner"
REFINER_TOOL_DISPLAY: Final[str] = "eCR Refiner"

# document source label -> from data augmentation document source value set (Vol 2 Table 3)
ORIGINAL_DOCUMENT_SOURCE: Final[str] = "original-document"


# NOTE:
# DETERMINISTIC SEEDING FOR AUGMENTED DOCUMENT IDENTIFIERS
# =============================================================================
#
# deterministic UUIDv5-based augmented identifiers; seed string shape:
#
#     {jurisdiction_id}|{condition_grouper_uuid}|{prefix:}{source}
#
# * condition_grouper_uuid is the UUID suffix extracted from the TES
# condition grouper's canonical_url (e.g.,
# https://tes.tools.aimsplatform.org/api/fhir/ValueSet/07221093-b8a1-4b1d-8678-259277bfba64
# yields 07221093-b8a1-4b1d-8678-259277bfba64)
# * seeding with the UUID alone--not the full URL--keeps the hash input stable against
# operational changes to the host or path that don't change the identity of the grouper
# * the UUID is the part TES guarantees will not change
#
# IMPORTANT:
# the namespace UUID, the seed prefix labels, the field separator,
# and the field ordering are all part of the wire-protocol contract
# and cannot be changed without breaking idempotency for every
# augmented document previously produced
#
# * see DIBBs-eCR-Refiner-Augmentation-Guide.md for: the full
# rationale, worked examples covering multi-jurisdiction and
# multi-condition cases, the wire-protocol contract details,
# and open IG questions tracked against this design

REFINER_DETERMINISTIC_NS: Final[uuid.UUID] = uuid.UUID(
    "cdcd1bb5-ecdc-4cdc-8cdc-d1bb5ecdc0dc"
)

_SEED_PREFIX_EICR_SETID: Final[str] = "eicr-setid"
_SEED_PREFIX_RR_SETID: Final[str] = "rr-setid"
_SEED_FIELD_SEPARATOR: Final[str] = "|"


def _extract_uuid_from_canonical_url(canonical_url: str) -> str:
    """
    Extract the trailing UUID from a TES condition grouper canonical_url.

    TES canonical URLs end with the UUID that uniquely identifies the
    condition grouper across versions. That UUID is the part we seed
    deterministic augmented identifiers from.

    Returns the UUID as it appears in the URL — no normalization. The
    Refiner treats the canonical_url as authoritative; whatever casing
    TES uses is what we seed with. URL shape validation lives at the
    data-ingest seam, not here.
    """

    return urlparse(canonical_url).path.rstrip("/").rsplit("/", 1)[-1]


def _derive_augmented_eicr_id(
    original_eicr_id_root: str,
    jurisdiction_id: str,
    condition_grouper_uuid: str,
) -> str:
    """
    Deterministic id for the augmented eICR.

    Same input pair + same (jurisdiction, condition) scope yields
    the same output (idempotent). See AUGMENT.md for the seed
    derivation rationale and worked examples.
    """

    return str(
        uuid.uuid5(
            REFINER_DETERMINISTIC_NS,
            f"{jurisdiction_id}{_SEED_FIELD_SEPARATOR}"
            f"{condition_grouper_uuid}{_SEED_FIELD_SEPARATOR}"
            f"{original_eicr_id_root}",
        )
    )


def _derive_augmented_rr_id(
    original_rr_id_root: str,
    jurisdiction_id: str,
    condition_grouper_uuid: str,
) -> str:
    """
    Deterministic id for the augmented RR.

    Same input pair + same (jurisdiction, condition) scope yields
    the same output (idempotent). See AUGMENT.md for the seed
    derivation rationale.
    """

    return str(
        uuid.uuid5(
            REFINER_DETERMINISTIC_NS,
            f"{jurisdiction_id}{_SEED_FIELD_SEPARATOR}"
            f"{condition_grouper_uuid}{_SEED_FIELD_SEPARATOR}"
            f"{original_rr_id_root}",
        )
    )


def _derive_augmented_eicr_setid(
    original_eicr_setid_root: str,
    jurisdiction_id: str,
    condition_grouper_uuid: str,
) -> str:
    """
    Deterministic setId for the augmented eICR.

    PHAs grouping by setId see one augmented setId per (jurisdiction,
    EHR conceptual document, condition) tuple, with versionNumber
    distinguishing iterations within the case. See AUGMENT.md for
    the seed derivation rationale.
    """

    return str(
        uuid.uuid5(
            REFINER_DETERMINISTIC_NS,
            f"{jurisdiction_id}{_SEED_FIELD_SEPARATOR}"
            f"{condition_grouper_uuid}{_SEED_FIELD_SEPARATOR}"
            f"{_SEED_PREFIX_EICR_SETID}:{original_eicr_setid_root}",
        )
    )


def _derive_augmented_rr_setid(
    original_eicr_setid_root: str,
    jurisdiction_id: str,
    condition_grouper_uuid: str,
) -> str:
    """
    Deterministic setId for the augmented RR.

    Note: seeds from the original *eICR's* setId, not the RR's. This
    gives PHAs pair recoverability — the augmented RR's setId is
    derivable from eICR-side identity alone (plus the scope
    discriminators). See AUGMENT.md §"Why both setIds seed from the
    eICR's setId" for rationale.
    """

    return str(
        uuid.uuid5(
            REFINER_DETERMINISTIC_NS,
            f"{jurisdiction_id}{_SEED_FIELD_SEPARATOR}"
            f"{condition_grouper_uuid}{_SEED_FIELD_SEPARATOR}"
            f"{_SEED_PREFIX_RR_SETID}:{original_eicr_setid_root}",
        )
    )


# NOTE:
# CONTEXT
# =============================================================================


@dataclass(frozen=True)
class AugmentationContext:
    """
    Pre-computed values needed to stamp an augmented eICR/RR pair.

    Created once per pair by the pipeline. Both augment_eicr and
    augment_rr read from this single context, which guarantees the
    augmented documents share effectiveTime and inherit versionNumber
    from the source eICR.

    The four augmented_* identifiers are deterministic UUIDv5
    derivations from the input pair, jurisdiction, and condition.
    augmentation_time conforms to DTM.US.FIELDED
    (urn:oid:2.16.840.1.113883.10.20.22.5.4) and is stamped on both
    documents' <effectiveTime> and on the augmentation author's
    <time>.

    Tool identity (the Data Augmentation Tool value set entry that
    identifies who produced the augmentation) is intentionally NOT
    on the context. It travels as a default-valued kwarg on
    augment_eicr / augment_rr — production callers always use the
    Refiner defaults, while tests can simulate prior augmentations
    by other tools without bypassing dataclass invariants.

    See DIBBs-eCR-Refiner-Augmentation-Guide.md for the
    seed-derivation rationale, the operational invariants this
    design rests on, and worked examples covering multi-jurisdiction
    and multi-condition cases.
    """

    augmented_eicr_id: str
    augmented_eicr_setid: str
    augmented_rr_id: str
    augmented_rr_setid: str
    augmentation_time: str
    version_number: str


def _create_augmentation_context(
    original_eicr_id_root: str,
    original_eicr_setid_root: str,
    original_eicr_version: str,
    original_rr_id_root: str,
    jurisdiction_id: str,
    condition_grouper_uuid: str,
    augmentation_time: str | None = None,
) -> AugmentationContext:
    """
    Build an AugmentationContext from raw input identifiers.

    Private — most callers should use create_augmentation_context_for_pair,
    which reads the four input identifiers off the parsed XML and
    extracts the condition grouper UUID from a canonical_url. This
    factory is the lower-level helper used by _for_pair and by tests
    that already have all the inputs in their derived form.

    See AUGMENT.md for the seed derivation rationale and for why
    jurisdiction_id and the condition grouper UUID are required scope
    discriminators.

    Args:
        original_eicr_id_root: The eICR's id/@root attribute value.
        original_eicr_setid_root: The eICR's setId/@root attribute
            value.
        original_eicr_version: The eICR's versionNumber/@value
            attribute value.
        original_rr_id_root: The RR's id/@root attribute value.
        jurisdiction_id: The jurisdiction code (e.g., "sddh", "lac")
            this refinement is scoped to. Comes from the RR's
            reportability metadata via the trace.
        condition_grouper_uuid: The UUID suffix from the TES condition
            grouper's canonical_url. The stable part TES guarantees
            won't change across versions.
        augmentation_time: Optional pre-formatted HL7 timestamp.
            When None, the current time is captured.

    Returns:
        A fully populated AugmentationContext ready for use by both
        augment_eicr and augment_rr.
    """

    if augmentation_time is None:
        now = datetime.now(UTC).astimezone()
        augmentation_time = now.strftime("%Y%m%d%H%M%S%z")

    return AugmentationContext(
        augmented_eicr_id=_derive_augmented_eicr_id(
            original_eicr_id_root, jurisdiction_id, condition_grouper_uuid
        ),
        augmented_eicr_setid=_derive_augmented_eicr_setid(
            original_eicr_setid_root, jurisdiction_id, condition_grouper_uuid
        ),
        augmented_rr_id=_derive_augmented_rr_id(
            original_rr_id_root, jurisdiction_id, condition_grouper_uuid
        ),
        augmented_rr_setid=_derive_augmented_rr_setid(
            original_eicr_setid_root, jurisdiction_id, condition_grouper_uuid
        ),
        augmentation_time=augmentation_time,
        version_number=original_eicr_version,
    )


def create_augmentation_context_for_pair(
    eicr_root: _Element,
    rr_root: _Element,
    jurisdiction_id: str,
    canonical_url: str,
    augmentation_time: str | None = None,
) -> AugmentationContext:
    """
    Read the four input identifiers off the parsed eICR/RR pair and build the AugmentationContext.

    The pipeline's natural entry point. The TES canonical_url is
    accepted as-is; this function extracts the trailing UUID suffix
    internally before feeding it into the deterministic derivation.
    Callers carry the full canonical_url because that's the
    domain-clear field name in our database (it matches
    conditions.canonical_url and configurations.condition_canonical_url),
    but only the UUID suffix participates in the hash.

    Args:
        eicr_root: The parsed eICR root element.
        rr_root: The parsed RR root element.
        jurisdiction_id: The jurisdiction code this refinement is
            scoped to.
        canonical_url: The TES condition grouper's canonical_url
            (e.g., "https://tes.tools.aimsplatform.org/api/fhir/
            ValueSet/07221093-b8a1-4b1d-8678-259277bfba64"). The
            UUID suffix is extracted and used as the stable seed.
        augmentation_time: Optional pre-formatted HL7 timestamp.
            When None, the current time is captured.

    Raises:
        ValueError: If the input eICR is missing setId or
            versionNumber (both required by eICR STU 3.1.1 and the
            augmentation IG v4 — CONF:5573-15, CONF:5573-16), or if
            canonical_url does not end with a valid UUID.
    """

    eicr_id_el = _find_required(eicr_root, "hl7:id")
    eicr_setid_el = eicr_root.find("hl7:setId", HL7_NS)
    eicr_version_el = eicr_root.find("hl7:versionNumber", HL7_NS)
    rr_id_el = _find_required(rr_root, "hl7:id")

    if eicr_setid_el is None:
        raise ValueError(
            "Cannot build augmentation context: input eICR has no "
            "<setId>. Required by eICR STU 3.1.1 and the augmentation "
            "IG v4 (CONF:5573-15)."
        )
    if eicr_version_el is None:
        raise ValueError(
            "Cannot build augmentation context: input eICR has no "
            "<versionNumber>. Required by eICR STU 3.1.1 and the "
            "augmentation IG v4 (CONF:5573-16)."
        )

    condition_grouper_uuid = _extract_uuid_from_canonical_url(canonical_url)

    return _create_augmentation_context(
        original_eicr_id_root=_get_attribute_value(eicr_id_el, "root"),
        original_eicr_setid_root=_get_attribute_value(eicr_setid_el, "root"),
        original_eicr_version=_get_attribute_value(eicr_version_el, "value"),
        original_rr_id_root=_get_attribute_value(rr_id_el, "root"),
        jurisdiction_id=jurisdiction_id,
        condition_grouper_uuid=condition_grouper_uuid,
        augmentation_time=augmentation_time,
    )


# NOTE:
# CAPTURED IDENTITY (for relatedDocument lineage)
# =============================================================================


@dataclass(frozen=True)
class _OriginalIdentity:
    """
    The document-identity elements captured from the input document before they are replaced.

    Used to build the new relatedDocument block we add for the input
    we just augmented, and to carry forward any prior relatedDocument
    blocks unchanged.

    set_id_element and version_number_element are None when the input
    lacked them. The relatedDocument builder honors that by omitting
    the corresponding child elements rather than synthesizing
    substitutes.
    """

    id_element: _Element
    set_id_element: _Element | None
    version_number_element: _Element | None
    prior_related_documents: list[_Element]


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
    tool_code: str = REFINER_TOOL_CODE,
    tool_display: str = REFINER_TOOL_DISPLAY,
) -> AugmentedResult:
    """
    Apply document-level augmentation to a refined eICR.

    Mutates `eicr_root` in place. Implements the eICR Data
    Augmentation Header template (Vol 2 §1.1).

    The steps execute in CDA R2 schema order: templateId → id →
    effectiveTime → setId → versionNumber → author → relatedDocument.

    tool_code and tool_display default to the Refiner's identity from
    the Data Augmentation Tool value set (Vol 2 Table 2). Production
    callers always use the defaults; tests may override to simulate
    augmentations performed by other tools.
    """

    # STEP 1: snapshot identity before overwriting
    original = _capture_original_identity(eicr_root)

    # STEP 2: add eICR augmentation templateId (CONF:5573-18/19/20)
    _add_augmentation_template_id(
        eicr_root,
        EICR_AUG_HEADER_TEMPLATE_ROOT,
        EICR_AUG_HEADER_TEMPLATE_EXT,
    )

    # STEP 3: replace document id
    augmented_result = _replace_document_id(
        eicr_root,
        new_doc_id=context.augmented_eicr_id,
        assigning_authority_name=tool_code,
    )

    # STEP 4: replace effectiveTime
    _replace_effective_time(eicr_root, context.augmentation_time)

    # STEP 5: replace setId
    _replace_set_id(eicr_root, context.augmented_eicr_setid, tool_code)

    # STEP 6: set versionNumber (inherited from source eICR)
    _replace_version_number(eicr_root, context.version_number)

    # STEP 7: add header-level augmentation author
    _add_augmentation_author(eicr_root, context, tool_code, tool_display)

    # STEP 8: restructure relatedDocument chain into v4-shape siblings
    _add_related_document(eicr_root, original)

    return augmented_result


# NOTE:
# PUBLIC API — RR
# =============================================================================


def augment_rr(
    rr_root: _Element,
    context: AugmentationContext,
    tool_code: str = REFINER_TOOL_CODE,
    tool_display: str = REFINER_TOOL_DISPLAY,
) -> AugmentedResult:
    """
    Apply document-level augmentation to a refined RR.

    Mutates `rr_root` in place. Implements the RR Data Augmentation
    Header template (Vol 2 §1.2), introduced in IG v4.

    Mirrors augment_eicr's eight-step structure with RR-specific
    identifiers and templateId. setId and versionNumber are
    replaced unconditionally — under v4 they are 1..1 SHALL on the
    augmented document, regardless of whether the input RR had them.

    tool_code and tool_display default to the Refiner's identity from
    the Data Augmentation Tool value set (Vol 2 Table 2). Production
    callers always use the defaults; tests may override to simulate
    augmentations performed by other tools.
    """

    # STEP 1: snapshot identity before overwriting
    original = _capture_original_identity(rr_root)

    # STEP 2: add RR augmentation templateId (CONF:5573-66/80/81)
    _add_augmentation_template_id(
        rr_root,
        RR_AUG_HEADER_TEMPLATE_ROOT,
        RR_AUG_HEADER_TEMPLATE_EXT,
    )

    # STEP 3: replace document id
    augmented_result = _replace_document_id(
        rr_root,
        new_doc_id=context.augmented_rr_id,
        assigning_authority_name=tool_code,
    )

    # STEP 4: replace effectiveTime
    _replace_effective_time(rr_root, context.augmentation_time)

    # STEP 5: replace setId (unconditional under v4)
    _replace_set_id(rr_root, context.augmented_rr_setid, tool_code)

    # STEP 6: set versionNumber (inherited from source eICR; unconditional under v4)
    _replace_version_number(rr_root, context.version_number)

    # STEP 7: add header-level augmentation author
    _add_augmentation_author(rr_root, context, tool_code, tool_display)

    # STEP 8: restructure relatedDocument chain into v4-shape siblings
    _add_related_document(rr_root, original)

    return augmented_result


# NOTE:
# PRIVATE HELPERS — IDENTITY CAPTURE
# =============================================================================


def _capture_original_identity(doc_root: _Element) -> _OriginalIdentity:
    """
    Snapshot the input document's identity elements before replacement.

    Captures three things:
        1. The document's own id, setId, versionNumber. setId and
           versionNumber are captured as None when missing (both are
           optional in CDA R2 and commonly absent on RRs from RCKMS).
        2. All prior relatedDocument[@typeCode='XFRM'] elements,
           verbatim. Carried forward into the augmented document
           unchanged — we don't inspect or rebuild them.

    Works for both eICR and RR documents.
    """

    doc_id = _find_required(doc_root, "hl7:id")
    set_id = doc_root.find("hl7:setId", HL7_NS)
    version = doc_root.find("hl7:versionNumber", HL7_NS)
    prior_related_docs = doc_root.findall(
        "hl7:relatedDocument[@typeCode='XFRM']", HL7_NS
    )

    return _OriginalIdentity(
        id_element=deepcopy(doc_id),
        set_id_element=deepcopy(set_id) if set_id is not None else None,
        version_number_element=deepcopy(version) if version is not None else None,
        prior_related_documents=[deepcopy(rd) for rd in prior_related_docs],
    )


# NOTE:
# PRIVATE HELPERS — ELEMENT REPLACEMENT
# =============================================================================


def _add_augmentation_template_id(
    doc_root: _Element,
    template_root: str,
    template_extension: str,
) -> None:
    """
    Insert an augmentation-header templateId on the document.

    Used for both the eICR Data Augmentation Header
    (root=2.16.840.1.113883.10.20.15.2.1.3, ext=2025-11-01) and the RR
    Data Augmentation Header (root=2.16.840.1.113883.10.20.15.2.1.4,
    ext=2026-04-01).

    Placed immediately before the document <id>, after any existing
    templateId elements, to maintain CDA schema element ordering.
    """

    new_template_id = _make_element(
        "templateId",
        root=template_root,
        extension=template_extension,
    )

    # insert just before <id> — all templateIds precede <id> in the CDA schema
    doc_id = _find_required(doc_root, "hl7:id")
    doc_id.addprevious(new_template_id)


def _replace_document_id(
    doc_root: _Element,
    new_doc_id: str,
    assigning_authority_name: str,
) -> AugmentedResult:
    """
    Replace the document <id> with a new id root and assigningAuthorityName.

    The assigningAuthorityName is drawn from the Data Augmentation
    Document Source value set, we use "ecr-refiner" for
    Refiner-produced documents.
    """

    old_id = _find_required(doc_root, "hl7:id")

    new_id = _make_element(
        "id",
        root=new_doc_id,
        assigningAuthorityName=assigning_authority_name,
    )

    _replace_preserving_tail(doc_root, old_id, new_id)

    return AugmentedResult(
        original_doc_id=_get_attribute_value(old_id, "root"),
        augmented_doc_id=_get_attribute_value(new_id, "root"),
    )


def _replace_effective_time(doc_root: _Element, augmentation_time: str) -> None:
    """
    Replace the document <effectiveTime> with the augmentation timestamp.
    """

    old_eff = _find_required(doc_root, "hl7:effectiveTime")
    new_eff = _make_element("effectiveTime", value=augmentation_time)
    _replace_preserving_tail(doc_root, old_eff, new_eff)


def _replace_set_id(
    doc_root: _Element,
    new_set_id_root: str,
    assigning_authority_name: str,
) -> None:
    """
    Replace or insert the document <setId>.

    The augmented setId carries assigningAuthorityName from the Data
    Augmentation Document Source value set (we use "ecr-refiner"
    for Refiner-produced documents).

    If <setId> doesn't exist (optional in CDA R2), inserts one in the
    correct schema position: after <languageCode> or
    <confidentialityCode>, before <versionNumber> or <recordTarget>.
    """

    new_set_id = _make_element(
        "setId",
        root=new_set_id_root,
        assigningAuthorityName=assigning_authority_name,
    )
    old_set_id = doc_root.find("hl7:setId", HL7_NS)

    if old_set_id is not None:
        _replace_preserving_tail(doc_root, old_set_id, new_set_id)
    else:
        _insert_before_first_found(
            doc_root,
            new_set_id,
            ["hl7:versionNumber", "hl7:recordTarget"],
        )


def _replace_version_number(doc_root: _Element, version_value: str) -> None:
    """
    Replace or insert <versionNumber>.

    The augmented document inherits versionNumber from the source
    eICR (passed in via the AugmentationContext), so an augmented
    eICR/RR pair tracks the EHR's clinical-case versioning stream.

    If <versionNumber> doesn't exist (optional in CDA R2), inserts
    one in the correct schema position: after <setId>, before
    <recordTarget>.
    """

    new_version = _make_element("versionNumber", value=version_value)
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


def _add_augmentation_author(
    doc_root: _Element,
    context: AugmentationContext,
    tool_code: str,
    tool_display: str,
) -> None:
    """
    Add the header-level augmentation author per IG v4.

    The eICR and RR augmentation headers share the same author shape,
    so a single helper produces a conformant author for both. Tool
    identity is carried via softwareName's coded attributes (no
    functionCode at the header level under v4).

    The author is appended after any existing <author> elements per
    CDA R2 element ordering.
    """

    ns = HL7_NAMESPACE

    author = _make_element("author")

    # time -> augmentation operation timestamp
    time_el = etree.SubElement(author, f"{{{ns}}}time")
    time_el.set("value", context.augmentation_time)

    # assignedAuthor
    assigned_author = etree.SubElement(author, f"{{{ns}}}assignedAuthor")

    # id, addr, telecom: nullFlavor="NA"
    _add_null_flavor_child(assigned_author, "id")
    _add_null_flavor_child(assigned_author, "addr")
    _add_null_flavor_child(assigned_author, "telecom")

    # assignedAuthoringDevice
    device = etree.SubElement(assigned_author, f"{{{ns}}}assignedAuthoringDevice")

    # softwareName — carries tool identity via coded attributes from
    # the Data Augmentation Tool value set
    software_name = etree.SubElement(device, f"{{{ns}}}softwareName")
    software_name.set("code", tool_code)
    software_name.set("codeSystem", ECR_DATA_AUG_CODE_SYSTEM)
    software_name.set("codeSystemName", ECR_DATA_AUG_CODE_SYSTEM_NAME)
    software_name.set("displayName", tool_display)

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
    Replace the relatedDocument chain with v4-shaped sibling blocks.

    Per IG v4 (Vol 2 §1.1 / §1.2), each prior augmentation contributes
    its own <relatedDocument> sibling rather than appending an <id>
    to a shared parentDocument.

    Steps:
        1. Remove all existing relatedDocument[@typeCode='XFRM'] from
           the document.
        2. Build a new relatedDocument for the input we just
           augmented.
        3. Insert prior relatedDocuments first (verbatim, preserving
           original order), then the new sibling, in the correct CDA
           schema position (after custodian, before componentOf).
    """

    # 1. clear existing
    for old in doc_root.findall("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS):
        doc_root.remove(old)

    # 2. build the new sibling for the input we just augmented
    new_related_doc = _build_related_document_for_input(original)

    # 3. insert prior siblings (verbatim) first, then the new one. each
    #    call to _insert_related_document inserts before componentOf
    #    (or component as fallback), and repeated calls produce
    #    siblings in call order at that position.
    for prior in original.prior_related_documents:
        _insert_related_document(doc_root, prior)
    _insert_related_document(doc_root, new_related_doc)


def _build_related_document_for_input(original: _OriginalIdentity) -> _Element:
    """
    Build a v4-shape <relatedDocument> referencing the input we just augmented.

    Honestly emits whatever identity the input had — id is always
    present (every CDA document has one), setId and versionNumber
    are emitted only when the input had them.

    When the input lacks setId or versionNumber (common for RRs),
    the parentDocument block omits those children. This is
    a deliberate violation of v4 CONF:5573-77 / CONF:5573-78.

    assigningAuthorityName values:
        - Original input (no prior relatedDocs): id and setId carry
          "original-document".
        - Augmented input: id carries the input's own authority;
          setId inherits its own authority if set, else falls back
          to the id's authority, else to "original-document".
    """

    is_original = not original.prior_related_documents

    related_doc = _make_element("relatedDocument", typeCode="XFRM")
    parent_doc = etree.SubElement(related_doc, f"{{{HL7_NAMESPACE}}}parentDocument")

    # id — always present; every CDA document has one
    id_for_parent = deepcopy(original.id_element)
    if is_original:
        id_authority = ORIGINAL_DOCUMENT_SOURCE
    else:
        id_authority = (
            id_for_parent.get("assigningAuthorityName") or ORIGINAL_DOCUMENT_SOURCE
        )
    id_for_parent.set("assigningAuthorityName", id_authority)
    parent_doc.append(id_for_parent)

    # setId — emit only when input had one
    if original.set_id_element is not None:
        set_id_for_parent = deepcopy(original.set_id_element)
        if is_original:
            setid_authority = ORIGINAL_DOCUMENT_SOURCE
        else:
            setid_authority = (
                set_id_for_parent.get("assigningAuthorityName") or id_authority
            )
        set_id_for_parent.set("assigningAuthorityName", setid_authority)
        parent_doc.append(set_id_for_parent)

    # versionNumber — emit only when input had one
    if original.version_number_element is not None:
        parent_doc.append(deepcopy(original.version_number_element))

    return related_doc


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


def _get_attribute_value(node: _Element, key: str) -> str:
    """
    Helper to convert an XML attribute to a string value.

    Args:
        node (_Element): XML node
        key (str): The attribute to grab the value from

    Raises:
        ValueError: Unable to get the value using the given key

    Returns:
        str: The value from the attribute
    """

    value = node.get(key)
    if not value:
        raise ValueError("Cannot convert XML to string. No value found at key {key}.")
    return value

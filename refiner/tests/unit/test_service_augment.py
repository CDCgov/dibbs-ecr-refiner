from lxml import etree

from app.services.ecr.augment import (
    AugmentationContext,
    _derive_augmented_eicr_id,
    _derive_augmented_eicr_setid,
    _derive_augmented_rr_id,
    _derive_augmented_rr_setid,
    augment_eicr,
    augment_rr,
    create_augmentation_context,
)
from app.services.ecr.model import HL7_NS

# NOTE:
# HELPERS
# =============================================================================


def _make_context(**overrides) -> AugmentationContext:
    """
    Creates a deterministic AugmentationContext for testing.

    Uses fixed values so assertions don't depend on UUIDs or wall-clock
    time. The four augmented identifiers default to recognizable
    placeholder strings rather than real UUIDv5 derivations — tests
    that need real derivations should construct a context via
    create_augmentation_context with known input identifiers, or
    override the relevant fields here.
    """

    defaults = {
        "augmented_eicr_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "augmented_eicr_setid": "11111111-2222-3333-4444-555555555555",
        "augmented_rr_id": "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee",
        "augmented_rr_setid": "99999999-2222-3333-4444-555555555555",
        "augmentation_time": "20260325120000+0000",
        "version_number": "1",
        "tool_code": "ecr-refiner",
        "tool_display": "eCR Refiner",
    }
    defaults.update(overrides)
    return AugmentationContext(**defaults)


# NOTE:
# EICR AUGMENTATION TESTS
# =============================================================================


def test_augment_eicr_adds_template_id(eicr_root_v1_1: etree.Element):
    """
    The eICR augmentation templateId should be added before the document id.
    """

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    template_ids = eicr_root_v1_1.xpath(
        "hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.1.3']",
        namespaces=HL7_NS,
    )
    assert len(template_ids) == 1
    assert template_ids[0].get("extension") == "2025-11-01"


def test_augment_eicr_replaces_document_id(eicr_root_v1_1: etree.Element):
    """
    The document id should be replaced with the augmented_eicr_id from
    the context, with assigningAuthorityName set to the tool code.
    """

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    doc_id = eicr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id is not None
    assert doc_id.get("root") == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert doc_id.get("assigningAuthorityName") == "ecr-refiner"


def test_augment_eicr_replaces_set_id_and_version(eicr_root_v1_1: etree.Element):
    """
    setId should get the augmented_eicr_setid and versionNumber should
    inherit from the context (which the pipeline supplies from the
    source eICR).
    """

    context = _make_context(version_number="3")
    augment_eicr(eicr_root_v1_1, context)

    set_id = eicr_root_v1_1.find("hl7:setId", HL7_NS)
    assert set_id is not None
    assert set_id.get("root") == "11111111-2222-3333-4444-555555555555"

    version = eicr_root_v1_1.find("hl7:versionNumber", HL7_NS)
    assert version is not None
    assert version.get("value") == "3"


def test_augment_eicr_adds_author(eicr_root_v1_1: etree.Element):
    """
    A new author should be added with the v4 shape:
      - NO functionCode (removed per Vol 1 change log 2026-03-10)
      - softwareName carries coded attributes from the Data
        Augmentation Tool value set
      - id, addr, telecom each have nullFlavor="NA"
    """

    context = _make_context()

    # count existing authors before augmentation
    authors_before = len(eicr_root_v1_1.findall("hl7:author", HL7_NS))

    augment_eicr(eicr_root_v1_1, context)

    authors_after = eicr_root_v1_1.findall("hl7:author", HL7_NS)
    assert len(authors_after) == authors_before + 1

    # the new author should be the last one
    new_author = authors_after[-1]

    # v4: no functionCode at the header level
    assert new_author.find("hl7:functionCode", HL7_NS) is None

    # softwareName carries coded attributes
    software_name = new_author.find(
        ".//hl7:assignedAuthoringDevice/hl7:softwareName", HL7_NS
    )
    assert software_name is not None
    assert software_name.get("code") == "ecr-refiner"
    assert software_name.get("codeSystem") == "2.16.840.1.113883.10.20.15.2.7.1"
    assert software_name.get("codeSystemName") == "eCRDataAugmentation"
    assert software_name.get("displayName") == "eCR Refiner"

    # nullFlavor elements
    assigned_author = new_author.find("hl7:assignedAuthor", HL7_NS)
    assert assigned_author.find("hl7:id", HL7_NS).get("nullFlavor") == "NA"
    assert assigned_author.find("hl7:addr", HL7_NS).get("nullFlavor") == "NA"
    assert assigned_author.find("hl7:telecom", HL7_NS).get("nullFlavor") == "NA"


def test_augment_eicr_adds_related_document(eicr_root_v1_1: etree.Element):
    """
    For an original-input eICR, exactly one relatedDocument sibling
    should be added with typeCode XFRM. Its parentDocument should
    contain the original document's id, setId, and versionNumber, with
    assigningAuthorityName="original-document" on both id and setId.
    """

    # capture the original identity before augmentation
    original_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")
    original_setid = eicr_root_v1_1.find("hl7:setId", HL7_NS).get("root")
    original_version = eicr_root_v1_1.find("hl7:versionNumber", HL7_NS).get("value")

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    related_docs = eicr_root_v1_1.findall(
        "hl7:relatedDocument[@typeCode='XFRM']", HL7_NS
    )
    assert len(related_docs) == 1

    parent_doc = related_docs[0].find("hl7:parentDocument", HL7_NS)
    assert parent_doc is not None

    parent_id = parent_doc.find("hl7:id", HL7_NS)
    assert parent_id is not None
    assert parent_id.get("root") == original_id
    assert parent_id.get("assigningAuthorityName") == "original-document"

    parent_setid = parent_doc.find("hl7:setId", HL7_NS)
    assert parent_setid is not None
    assert parent_setid.get("root") == original_setid
    assert parent_setid.get("assigningAuthorityName") == "original-document"

    parent_version = parent_doc.find("hl7:versionNumber", HL7_NS)
    assert parent_version is not None
    assert parent_version.get("value") == original_version


def test_augment_eicr_replaces_effective_time(eicr_root_v1_1: etree.Element):
    """
    effectiveTime should be replaced with the augmentation timestamp.
    """

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    eff_time = eicr_root_v1_1.find("hl7:effectiveTime", HL7_NS)
    assert eff_time is not None
    assert eff_time.get("value") == "20260325120000+0000"


# NOTE:
# RR AUGMENTATION TESTS
# =============================================================================


def test_augment_rr_adds_rr_augmentation_template_id(rr_root_v1_1: etree.Element):
    """
    Under v4, the RR gets its own augmentation header template
    (Vol 1 §2, Vol 2 §1.2), distinct from the eICR's. The RR
    augmentation templateId is 2.16.840.1.113883.10.20.15.2.1.4 with
    extension 2026-04-01.
    """

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    rr_aug_template = rr_root_v1_1.xpath(
        "hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.1.4']",
        namespaces=HL7_NS,
    )
    assert len(rr_aug_template) == 1
    assert rr_aug_template[0].get("extension") == "2026-04-01"

    # the eICR augmentation templateId should NOT appear on the RR —
    # they're distinct templates with distinct CONF numbers
    eicr_aug_template = rr_root_v1_1.xpath(
        "hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.1.3']",
        namespaces=HL7_NS,
    )
    assert len(eicr_aug_template) == 0


def test_augment_rr_replaces_set_id_and_version_unconditionally(
    rr_root_v1_1: etree.Element,
):
    """
    Under v4 RR augmentation header (CONF:5573-77/78), setId and
    versionNumber are 1..1 SHALL on the augmented RR — they are added
    even if the input RR didn't have them.

    The augmented RR's identifiers come from the pair-aware context's
    RR-side fields. versionNumber inherits from the eICR via
    context.version_number.
    """

    context = _make_context(version_number="3")
    augment_rr(rr_root_v1_1, context)

    set_id = rr_root_v1_1.find("hl7:setId", HL7_NS)
    assert set_id is not None
    assert set_id.get("root") == "99999999-2222-3333-4444-555555555555"

    version = rr_root_v1_1.find("hl7:versionNumber", HL7_NS)
    assert version is not None
    assert version.get("value") == "3"


def test_augment_rr_replaces_document_id(rr_root_v1_1: etree.Element):
    """
    The RR's document id should come from context.augmented_rr_id (not
    augmented_eicr_id), with the tool code as authority name.
    """

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    doc_id = rr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id is not None
    assert doc_id.get("root") == "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert doc_id.get("assigningAuthorityName") == "ecr-refiner"


def test_augment_rr_adds_author_and_related_document(rr_root_v1_1: etree.Element):
    """
    The RR should get a v4-shape author and relatedDocument: author
    has no functionCode, softwareName has coded attrs, and the
    relatedDocument's parentDocument carries the original RR's id with
    assigningAuthorityName="original-document".
    """

    original_id = rr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    # author added with v4 shape
    authors = rr_root_v1_1.findall("hl7:author", HL7_NS)
    assert any(
        a.find("hl7:functionCode", HL7_NS) is None
        and a.find(".//hl7:assignedAuthoringDevice/hl7:softwareName", HL7_NS)
        is not None
        and a.find(".//hl7:assignedAuthoringDevice/hl7:softwareName", HL7_NS).get(
            "code"
        )
        == "ecr-refiner"
        for a in authors
    )

    # relatedDocument referencing the original RR
    related_doc = rr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    assert related_doc is not None
    parent_id = related_doc.find("hl7:parentDocument/hl7:id", HL7_NS)
    assert parent_id.get("root") == original_id
    assert parent_id.get("assigningAuthorityName") == "original-document"


def test_augment_rr_relatedDocument_omits_setId_and_version_when_input_lacks_them(
    rr_root_v1_1: etree.Element,
):
    """
    When the input RR lacks <setId> and <versionNumber>, the augmented
    RR's relatedDocument/parentDocument also lacks those elements —
    we don't synthesize identity for documents we didn't author.

    This deliberately violates v4 CONF:5573-77 / CONF:5573-78
    cardinality on parentDocument/setId and parentDocument/
    versionNumber. The structural absence is the audit-trail signal
    that the original RR lacked the field. See
    _build_related_document_for_input docstring for rationale.

    The augmented document's *own* setId and versionNumber are still
    populated — those come from the AugmentationContext (derived from
    the eICR's identity), not from the original RR's identity.
    """

    # confirm the fixture matches the assumption — these fields are
    # commonly absent on real RRs from RCKMS, which is the scenario
    # this test pins
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is None

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    # augmented document itself has setId and versionNumber from
    # the context (derived from the eICR-side identity)
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is not None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is not None

    # but the parentDocument block faithfully omits them
    related_doc = rr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    parent_doc = related_doc.find("hl7:parentDocument", HL7_NS)

    assert parent_doc.find("hl7:id", HL7_NS) is not None
    assert parent_doc.find("hl7:setId", HL7_NS) is None
    assert parent_doc.find("hl7:versionNumber", HL7_NS) is None


# NOTE:
# CHAINING TESTS — v4 N-sibling shape
# =============================================================================


def test_augment_eicr_chains_prior_relatedDocs_as_siblings(
    eicr_root_v1_1: etree.Element,
):
    """
    Under v4, when an already-augmented eICR is augmented again, the
    output document carries N relatedDocument siblings rather than one
    block with a cumulative id list. The prior relatedDocument(s) are
    preserved verbatim and a new one is added for the augmentation we
    just performed.

    Per Vol 2 Figure 2, the original-document-pointing block appears
    first, followed by augmentation siblings in chronological order.
    """

    # first augmentation simulates a prior tool (e.g., text-to-code)
    first_context = _make_context(
        augmented_eicr_id="first-augmented-id",
        augmented_eicr_setid="first-set-id",
        tool_code="text-to-code",
        tool_display="Text-to-Code",
    )
    original_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    augment_eicr(eicr_root_v1_1, first_context)

    # second augmentation simulates the Refiner running on the prior output
    second_ctx = _make_context(
        augmented_eicr_id="second-augmented-id",
        augmented_eicr_setid="second-set-id",
        tool_code="ecr-refiner",
        tool_display="eCR Refiner",
    )
    augment_eicr(eicr_root_v1_1, second_ctx)

    # there should be two relatedDocument siblings now
    related_docs = eicr_root_v1_1.findall(
        "hl7:relatedDocument[@typeCode='XFRM']", HL7_NS
    )
    assert len(related_docs) == 2

    # first sibling: the original-document pointer (preserved verbatim
    # from the first augmentation)
    first_sibling_id = related_docs[0].find("hl7:parentDocument/hl7:id", HL7_NS)
    assert first_sibling_id.get("root") == original_id
    assert first_sibling_id.get("assigningAuthorityName") == "original-document"

    # second sibling: the new one we just built, pointing at the
    # output of the first augmentation (which we treated as the input
    # to the second augmentation)
    second_sibling_id = related_docs[1].find("hl7:parentDocument/hl7:id", HL7_NS)
    assert second_sibling_id.get("root") == "first-augmented-id"
    assert second_sibling_id.get("assigningAuthorityName") == "text-to-code"

    # second sibling also carries the prior augmentation's setId and version
    second_sibling_setid = related_docs[1].find("hl7:parentDocument/hl7:setId", HL7_NS)
    assert second_sibling_setid.get("root") == "first-set-id"
    assert second_sibling_setid.get("assigningAuthorityName") == "text-to-code"


# NOTE:
# CONTEXT FACTORY TESTS — deterministic identifiers
# =============================================================================


def test_create_augmentation_context_is_deterministic():
    """
    Per IG v4 Vol 1 Appendix A, augmented identifiers are deterministic
    content-based GUIDs. Two contexts created from the same input
    identifiers should produce identical augmented identifiers.
    """

    common = {
        "original_eicr_id_root": "orig-eicr-1234",
        "original_eicr_setid_root": "orig-set-2222",
        "original_eicr_version": "3",
        "original_rr_id_root": "orig-rr-5678",
        "jurisdiction_id": "SDDH",
        "condition_grouper_name": "COVID-19",
        "augmentation_time": "20260101120000+0000",
    }
    context_1 = create_augmentation_context(**common)
    context_2 = create_augmentation_context(**common)

    assert context_1.augmented_eicr_id == context_2.augmented_eicr_id
    assert context_1.augmented_eicr_setid == context_2.augmented_eicr_setid
    assert context_1.augmented_rr_id == context_2.augmented_rr_id
    assert context_1.augmented_rr_setid == context_2.augmented_rr_setid


def test_create_augmentation_context_distinct_inputs_distinct_outputs():
    """
    Different input identifiers should produce different augmented
    identifiers. Specifically:
      - The augmented eICR id and augmented RR id seed from different
        sources (the eICR's id vs the RR's id) and must be distinct.
      - The augmented eICR setId and augmented RR setId seed from the
        same source (the eICR's setId) but with different prefix
        labels; they must also be distinct.
    """

    context = create_augmentation_context(
        original_eicr_id_root="orig-eicr-1234",
        original_eicr_setid_root="orig-set-2222",
        original_eicr_version="3",
        original_rr_id_root="orig-rr-5678",
        jurisdiction_id="SDDH",
        condition_grouper_name="COVID-19",
        augmentation_time="20260101120000+0000",
    )

    assert context.augmented_eicr_id != context.augmented_rr_id
    assert context.augmented_eicr_setid != context.augmented_rr_setid


def test_create_augmentation_context_pair_recoverability():
    """
    A PHA holding the original eICR's setId can derive the augmented
    RR's setId without seeing the RR — given the condition grouper
    name. This pair-recoverability property is what justifies seeding
    the augmented RR setId from the eICR's setId rather than the
    RR's.
    """

    eicr_setid = "orig-set-2222"

    # PHA-side derivation using only the eICR setId and the condition
    derived_directly = _derive_augmented_rr_setid(eicr_setid, "SDDH", "COVID-19")

    # Refiner-side derivation via the full context
    context = create_augmentation_context(
        original_eicr_id_root="orig-eicr-1234",
        original_eicr_setid_root=eicr_setid,
        original_eicr_version="3",
        original_rr_id_root="orig-rr-5678",
        jurisdiction_id="SDDH",
        condition_grouper_name="COVID-19",
        augmentation_time="20260101120000+0000",
    )

    assert derived_directly == context.augmented_rr_setid


def test_create_augmentation_context_inherits_version_number():
    """
    The context's version_number is the input eICR's version, not a
    Refiner-invented value. Both the augmented eICR and augmented RR
    are stamped with this version, so the augmented pair's
    versionNumber tracks the EHR's clinical-case versioning stream.
    """

    context = create_augmentation_context(
        original_eicr_id_root="orig-eicr-1234",
        original_eicr_setid_root="orig-set-2222",
        original_eicr_version="7",
        original_rr_id_root="orig-rr-5678",
        jurisdiction_id="SDDH",
        condition_grouper_name="COVID-19",
        augmentation_time="20260101120000+0000",
    )

    assert context.version_number == "7"


def test_create_augmentation_context_shared_timestamp():
    """
    When augmentation_time is passed, it should be used instead of
    capturing the clock. This is how the pipeline ensures the eICR
    and RR halves of a pair share an effectiveTime.
    """

    shared_time = "20260101120000+0000"
    context = create_augmentation_context(
        original_eicr_id_root="orig-eicr-1234",
        original_eicr_setid_root="orig-set-2222",
        original_eicr_version="3",
        original_rr_id_root="orig-rr-5678",
        jurisdiction_id="SDDH",
        condition_grouper_name="COVID-19",
        augmentation_time=shared_time,
    )

    assert context.augmentation_time == shared_time


# NOTE:
# DERIVATION HELPER TESTS
# =============================================================================


def test_derive_augmented_eicr_id_is_pure_function_of_inputs():
    """
    The eICR id derivation depends only on (original eICR id, condition
    grouper name) and produces deterministic output.
    """

    a = _derive_augmented_eicr_id("doc-1234", "SDDH", "COVID-19")
    b = _derive_augmented_eicr_id("doc-1234", "SDDH", "COVID-19")
    c = _derive_augmented_eicr_id("doc-5678", "SDDH", "COVID-19")
    d = _derive_augmented_eicr_id("doc-1234", "SDDH", "INFLUENZA")
    assert a == b  # same inputs → same output
    assert a != c  # different document id → different output
    assert a != d  # different condition → different output


def test_derive_augmented_eicr_setid_uses_prefix():
    """
    The eICR setId derivation prefixes the source value with
    "eicr-setid:" inside the seed string. Verifying that the
    derivation differs from a naked uuid5 of the source confirms the
    prefix is actually being used.
    """

    import uuid

    from app.services.ecr.augment import REFINER_DETERMINISTIC_NS

    naked = str(uuid.uuid5(REFINER_DETERMINISTIC_NS, "orig-set-2222"))
    prefixed = _derive_augmented_eicr_setid("orig-set-2222", "SDDH", "COVID-19")
    assert naked != prefixed


def test_derive_augmented_rr_setid_distinct_from_eicr_setid():
    """
    The RR setId derivation uses a different prefix than the eICR
    setId derivation. Given the same source value and condition,
    the two helpers produce different UUIDs.
    """

    source = "orig-set-2222"
    eicr_setid = _derive_augmented_eicr_setid(source, "SDDH", "COVID-19")
    rr_setid = _derive_augmented_rr_setid(source, "SDDH", "COVID-19")
    assert eicr_setid != rr_setid


def test_derive_helpers_discriminate_on_condition():
    """
    All four derivation helpers produce condition-discriminated output:
    given the same input identifier, two different condition grouper
    names produce two different UUIDs. This is the property that lets
    a single eICR/RR pair be refined for multiple conditions without
    producing colliding augmented identifiers.
    """

    eicr_id = _derive_augmented_eicr_id("doc-1234", "SDDH", "COVID-19")
    eicr_id_flu = _derive_augmented_eicr_id("doc-1234", "SDDH", "INFLUENZA")
    assert eicr_id != eicr_id_flu

    eicr_setid = _derive_augmented_eicr_setid("set-2222", "SDDH", "COVID-19")
    eicr_setid_flu = _derive_augmented_eicr_setid("set-2222", "SDDH", "INFLUENZA")
    assert eicr_setid != eicr_setid_flu

    rr_id = _derive_augmented_rr_id("rr-5678", "SDDH", "COVID-19")
    rr_id_flu = _derive_augmented_rr_id("rr-5678", "SDDH", "INFLUENZA")
    assert rr_id != rr_id_flu

    rr_setid = _derive_augmented_rr_setid("set-2222", "SDDH", "COVID-19")
    rr_setid_flu = _derive_augmented_rr_setid("set-2222", "SDDH", "INFLUENZA")
    assert rr_setid != rr_setid_flu


def test_derive_helpers_discriminate_on_jurisdiction():
    """
    All four derivation helpers produce jurisdiction-discriminated
    output: given the same input identifier and condition, two
    different jurisdiction codes produce two different UUIDs. This is
    the property that lets a single eICR/RR pair be refined for the
    same condition under multiple jurisdictions (e.g., LAC and CA for
    a Los Angeles encounter) without producing colliding augmented
    identifiers.
    """

    eicr_id_lac = _derive_augmented_eicr_id("doc-1234", "LAC", "COVID-19")
    eicr_id_ca = _derive_augmented_eicr_id("doc-1234", "CA", "COVID-19")
    assert eicr_id_lac != eicr_id_ca

    eicr_setid_lac = _derive_augmented_eicr_setid("set-2222", "LAC", "COVID-19")
    eicr_setid_ca = _derive_augmented_eicr_setid("set-2222", "CA", "COVID-19")
    assert eicr_setid_lac != eicr_setid_ca

    rr_id_lac = _derive_augmented_rr_id("rr-5678", "LAC", "COVID-19")
    rr_id_ca = _derive_augmented_rr_id("rr-5678", "CA", "COVID-19")
    assert rr_id_lac != rr_id_ca

    rr_setid_lac = _derive_augmented_rr_setid("set-2222", "LAC", "COVID-19")
    rr_setid_ca = _derive_augmented_rr_setid("set-2222", "CA", "COVID-19")
    assert rr_setid_lac != rr_setid_ca

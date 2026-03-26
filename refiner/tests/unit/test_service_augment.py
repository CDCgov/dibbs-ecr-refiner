from lxml import etree

from app.services.ecr.augment import (
    AugmentationContext,
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

    Uses fixed values so assertions don't depend on UUIDs or wall-clock time.
    """

    defaults = {
        "new_doc_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "new_set_id": "11111111-2222-3333-4444-555555555555",
        "augmentation_time": "20260325120000+0000",
        "tool_code": "ecr-refinement",
        "tool_display": "eCR Refiner",
    }
    defaults.update(overrides)
    return AugmentationContext(**defaults)


# NOTE:
# EICR AUGMENTATION TESTS
# =============================================================================


def test_augment_eicr_adds_template_id(eicr_root_v1_1: etree.Element):
    """
    The augmentation templateId should be added before the document id.
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
    The document id should be replaced with the new UUID and
    assigningAuthorityName from the context.
    """

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    doc_id = eicr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id is not None
    assert doc_id.get("root") == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert doc_id.get("assigningAuthorityName") == "ecr-refinement"


def test_augment_eicr_replaces_set_id_and_version(eicr_root_v1_1: etree.Element):
    """
    setId should get a new UUID and versionNumber should reset to 1.
    """

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    set_id = eicr_root_v1_1.find("hl7:setId", HL7_NS)
    assert set_id is not None
    assert set_id.get("root") == "11111111-2222-3333-4444-555555555555"

    version = eicr_root_v1_1.find("hl7:versionNumber", HL7_NS)
    assert version is not None
    assert version.get("value") == "1"


def test_augment_eicr_adds_author(eicr_root_v1_1: etree.Element):
    """
    A new author should be added with the correct functionCode,
    nullFlavor elements, and softwareName.
    """

    context = _make_context()

    # count existing authors before augmentation
    authors_before = len(eicr_root_v1_1.findall("hl7:author", HL7_NS))

    augment_eicr(eicr_root_v1_1, context)

    authors_after = eicr_root_v1_1.findall("hl7:author", HL7_NS)
    assert len(authors_after) == authors_before + 1

    # the new author should be the last one
    new_author = authors_after[-1]

    function_code = new_author.find("hl7:functionCode", HL7_NS)
    assert function_code is not None
    assert function_code.get("code") == "ecr-refinement"

    software_name = new_author.find(
        ".//hl7:assignedAuthoringDevice/hl7:softwareName", HL7_NS
    )
    assert software_name is not None
    assert software_name.get("displayName") == "Data Augmentation Tool"

    # nullFlavor elements
    assigned_author = new_author.find("hl7:assignedAuthor", HL7_NS)
    assert assigned_author.find("hl7:id", HL7_NS).get("nullFlavor") == "NA"
    assert assigned_author.find("hl7:addr", HL7_NS).get("nullFlavor") == "NA"
    assert assigned_author.find("hl7:telecom", HL7_NS).get("nullFlavor") == "NA"


def test_augment_eicr_adds_related_document(eicr_root_v1_1: etree.Element):
    """
    A relatedDocument with typeCode XFRM should be added, containing
    the original document's id with assigningAuthorityName="original-document".
    """

    # capture the original id before augmentation
    original_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    context = _make_context()
    augment_eicr(eicr_root_v1_1, context)

    related_doc = eicr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    assert related_doc is not None

    parent_doc = related_doc.find("hl7:parentDocument", HL7_NS)
    assert parent_doc is not None

    parent_id = parent_doc.find("hl7:id", HL7_NS)
    assert parent_id is not None
    assert parent_id.get("root") == original_id
    assert parent_id.get("assigningAuthorityName") == "original-document"


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


def test_augment_rr_skips_set_id_and_version_when_absent(rr_root_v1_1: etree.Element):
    """
    RRs typically lack setId and versionNumber. The augmentation should
    not fabricate them.
    """

    # confirm the fixture doesn't have them
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is None

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    # should still not have them after augmentation
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is None


def test_augment_rr_does_not_add_augmentation_template_id(rr_root_v1_1: etree.Element):
    """
    The augmentation templateId is eICR-specific and should NOT be added to the RR.
    """

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    aug_template = rr_root_v1_1.xpath(
        "hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.1.3']",
        namespaces=HL7_NS,
    )
    assert len(aug_template) == 0


def test_augment_rr_adds_author_and_related_document(rr_root_v1_1: etree.Element):
    """
    The RR should get a new author and relatedDocument just like the eICR.
    """

    original_id = rr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    context = _make_context()
    augment_rr(rr_root_v1_1, context)

    # new document id
    doc_id = rr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id.get("root") == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # author added
    authors = rr_root_v1_1.findall("hl7:author", HL7_NS)
    assert any(
        a.find("hl7:functionCode", HL7_NS) is not None
        and a.find("hl7:functionCode", HL7_NS).get("code") == "ecr-refinement"
        for a in authors
    )

    # relatedDocument with original id
    related_doc = rr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    assert related_doc is not None
    parent_id = related_doc.find("hl7:parentDocument/hl7:id", HL7_NS)
    assert parent_id.get("root") == original_id


# NOTE:
# CHAINING TESTS
# =============================================================================


def test_augment_eicr_chains_cumulative_ids(eicr_root_v1_1: etree.Element):
    """
    When an already-augmented eICR is augmented again, the relatedDocument
    should carry forward all prior IDs plus the intermediate document's ID.
    """

    # first augmentation (simulating text-to-code)
    first_context = _make_context(
        new_doc_id="first-augmented-id",
        new_set_id="first-set-id",
        tool_code="text-to-code",
    )
    original_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    augment_eicr(eicr_root_v1_1, first_context)

    # second augmentation (refiner)
    second_ctx = _make_context(
        new_doc_id="second-augmented-id",
        new_set_id="second-set-id",
        tool_code="ecr-refinement",
    )
    augment_eicr(eicr_root_v1_1, second_ctx)

    # the relatedDocument should have the cumulative chain
    related_doc = eicr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    parent_doc = related_doc.find("hl7:parentDocument", HL7_NS)
    parent_ids = parent_doc.findall("hl7:id", HL7_NS)

    # should have two IDs: original-document and text-to-code
    assert len(parent_ids) == 2

    id_roots = [pid.get("root") for pid in parent_ids]
    assert original_id in id_roots
    assert "first-augmented-id" in id_roots

    # verify assigningAuthorityName labels
    authority_names = [pid.get("assigningAuthorityName") for pid in parent_ids]
    assert "original-document" in authority_names
    assert "text-to-code" in authority_names


# NOTE:
# CONTEXT FACTORY TESTS
# =============================================================================


def test_create_augmentation_context_generates_unique_ids():
    """
    Each call should produce different UUIDs.
    """

    context_1 = create_augmentation_context()
    context_2 = create_augmentation_context()

    assert context_1.new_doc_id != context_2.new_doc_id
    assert context_1.new_set_id != context_2.new_set_id


def test_create_augmentation_context_shared_timestamp():
    """
    When augmentation_time is passed, it should be used instead of
    capturing the clock.
    """

    shared_time = "20260101120000+0000"
    context_1 = create_augmentation_context(augmentation_time=shared_time)
    context_2 = create_augmentation_context(augmentation_time=shared_time)

    assert context_1.augmentation_time == shared_time
    assert context_2.augmentation_time == shared_time
    assert context_1.new_doc_id != context_2.new_doc_id  # still unique IDs

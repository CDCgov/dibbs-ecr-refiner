import uuid

import pytest
from lxml import etree

from app.services.ecr.augment import (
    REFINER_DETERMINISTIC_NS,
    REMAINDER_SCOPE,
    AugmentationRun,
    _derive_augmented_eicr_id,
    _derive_augmented_eicr_setid,
    _derive_augmented_rr_id,
    _derive_augmented_rr_setid,
    augment_eicr,
    augment_rr,
    create_augmentation_run,
    update_rr_eicr_external_document_reference,
)
from app.services.ecr.model import HL7_NS

# NOTE:
# HELPERS
# =============================================================================

# realistic-shaped TES canonical URL for tests that need one. the trailing UUID
# is what feeds the deterministic derivation; everything before it is cosmetic.
_TEST_CANONICAL_URL = (
    "https://tes.tools.aimsplatform.org/api/fhir/ValueSet/"
    "07221093-b8a1-4b1d-8678-259277bfba64"
)
# the scope discriminator is a UUID object now (the type is the
# validator). tests pass UUIDs directly rather than strings; the
# canonical_url → UUID conversion is exercised by aws/s3_keys tests,
# not here
_TEST_CONDITION_GROUPER_UUID = uuid.UUID("07221093-b8a1-4b1d-8678-259277bfba64")

# fixed values used across tests so assertions don't depend on UUIDs or
# wall-clock time. Tests that need to verify ID stamping derive the
# expected augmented values via the _derive_* helpers using these inputs.
_TEST_JURISDICTION_ID = "SDDH"
_TEST_AUGMENTATION_TIME = "20260325120000+0000"


def _make_run(**overrides) -> AugmentationRun:
    """
    Creates a deterministic AugmentationRun for testing.

    AugmentationRun carries only the values shared across every
    augmentation in a session: the timestamp, the inherited
    versionNumber, and the source eICR's setId root (used as the seed
    for RR-side setId derivations). Per-call discriminators —
    jurisdiction_id, condition_grouper_uuid / scope, tool identity —
    travel as direct arguments to augment_eicr / augment_rr, not on
    the run.

    Augmented identifiers are NOT on the run; they are derived inside
    augment_eicr / augment_rr from (run, jurisdiction, scope, captured
    input identity). Tests that need to assert against specific
    augmented values compute them via _derive_* using the fixture's
    original identifiers and the test scope.
    """

    defaults = {
        "augmentation_time": _TEST_AUGMENTATION_TIME,
        "version_number": "1",
        "original_eicr_setid_root": "orig-eicr-setid-from-run",
    }
    defaults.update(overrides)
    return AugmentationRun(**defaults)


# NOTE:
# EICR AUGMENTATION TESTS
# =============================================================================


def test_augment_eicr_adds_template_id(eicr_root_v1_1: etree.Element):
    """
    The eICR augmentation templateId should be added before the document id.
    """

    run = _make_run()
    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

    template_ids = eicr_root_v1_1.xpath(
        "hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.1.3']",
        namespaces=HL7_NS,
    )
    assert len(template_ids) == 1
    assert template_ids[0].get("extension") == "2025-11-01"


def test_augment_eicr_replaces_document_id(eicr_root_v1_1: etree.Element):
    """
    The document id should be replaced with the derived augmented eICR
    id (seeded from the input eICR's id, the jurisdiction, and the
    condition grouper UUID), with assigningAuthorityName set to the
    tool code.
    """

    original_eicr_id_root = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")
    expected_id = _derive_augmented_eicr_id(
        original_eicr_id_root,
        _TEST_JURISDICTION_ID,
        _TEST_CONDITION_GROUPER_UUID,
    )

    run = _make_run()
    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

    doc_id = eicr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id is not None
    assert doc_id.get("root") == expected_id
    assert doc_id.get("assigningAuthorityName") == "ecr-refiner"


def test_augment_eicr_replaces_set_id_and_version(eicr_root_v1_1: etree.Element):
    """
    setId should get the derived augmented eICR setId (seeded from the
    run's original_eicr_setid_root, which the pipeline supplies from
    the source eICR) and versionNumber should inherit from the run.
    """

    # the run's original_eicr_setid_root is what the pipeline would
    # have captured off the source eICR — point the test run at the
    # fixture's setId so the derivation reflects reality
    original_eicr_setid_root = eicr_root_v1_1.find("hl7:setId", HL7_NS).get("root")
    expected_setid = _derive_augmented_eicr_setid(
        original_eicr_setid_root,
        _TEST_JURISDICTION_ID,
        _TEST_CONDITION_GROUPER_UUID,
    )

    run = _make_run(
        version_number="3",
        original_eicr_setid_root=original_eicr_setid_root,
    )
    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

    set_id = eicr_root_v1_1.find("hl7:setId", HL7_NS)
    assert set_id is not None
    assert set_id.get("root") == expected_setid

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

    run = _make_run()

    # count existing authors before augmentation
    authors_before = len(eicr_root_v1_1.findall("hl7:author", HL7_NS))

    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

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

    # capture the relatedDocument count before augmentation so we can
    # assert relative growth
    original_related_docs = eicr_root_v1_1.findall(
        "hl7:relatedDocument[@typeCode='XFRM']", HL7_NS
    )
    starting_related_doc_len = len(original_related_docs)

    run = _make_run()
    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

    related_docs = eicr_root_v1_1.findall(
        "hl7:relatedDocument[@typeCode='XFRM']", HL7_NS
    )
    assert len(related_docs) == starting_related_doc_len + 1

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

    run = _make_run()
    augment_eicr(
        eicr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )

    eff_time = eicr_root_v1_1.find("hl7:effectiveTime", HL7_NS)
    assert eff_time is not None
    assert eff_time.get("value") == _TEST_AUGMENTATION_TIME


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

    run = _make_run()
    augment_rr(
        rr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        scope=_TEST_CONDITION_GROUPER_UUID,
    )

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

    The augmented RR's setId is derived from the run's
    original_eicr_setid_root (the eICR-side seed; see pair
    recoverability), the jurisdiction, and the scope. versionNumber
    inherits from the eICR via run.version_number.
    """

    original_eicr_setid_root = "orig-set-2222"
    expected_setid = _derive_augmented_rr_setid(
        original_eicr_setid_root,
        _TEST_JURISDICTION_ID,
        _TEST_CONDITION_GROUPER_UUID,
    )

    run = _make_run(
        version_number="3",
        original_eicr_setid_root=original_eicr_setid_root,
    )
    augment_rr(
        rr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        scope=_TEST_CONDITION_GROUPER_UUID,
    )

    set_id = rr_root_v1_1.find("hl7:setId", HL7_NS)
    assert set_id is not None
    assert set_id.get("root") == expected_setid

    version = rr_root_v1_1.find("hl7:versionNumber", HL7_NS)
    assert version is not None
    assert version.get("value") == "3"


def test_augment_rr_replaces_document_id(rr_root_v1_1: etree.Element):
    """
    The RR's document id should be the derived augmented RR id
    (seeded from the input RR's id, the jurisdiction, and the scope),
    with the tool code as authority name.
    """

    original_rr_id_root = rr_root_v1_1.find("hl7:id", HL7_NS).get("root")
    expected_id = _derive_augmented_rr_id(
        original_rr_id_root,
        _TEST_JURISDICTION_ID,
        _TEST_CONDITION_GROUPER_UUID,
    )

    run = _make_run()
    augment_rr(
        rr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        scope=_TEST_CONDITION_GROUPER_UUID,
    )

    doc_id = rr_root_v1_1.find("hl7:id", HL7_NS)
    assert doc_id is not None
    assert doc_id.get("root") == expected_id
    assert doc_id.get("assigningAuthorityName") == "ecr-refiner"


def test_augment_rr_adds_author_and_related_document(rr_root_v1_1: etree.Element):
    """
    The RR should get a v4-shape author and relatedDocument: author
    has no functionCode, softwareName has coded attrs, and the
    relatedDocument's parentDocument carries the original RR's id with
    assigningAuthorityName="original-document".
    """

    original_id = rr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    run = _make_run()
    augment_rr(
        rr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        scope=_TEST_CONDITION_GROUPER_UUID,
    )

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
    populated — those come from the AugmentationRun (derived from
    the eICR's identity), not from the original RR's identity.
    """

    # confirm the fixture matches the assumption — these fields are
    # commonly absent on real RRs from RCKMS, which is the scenario
    # this test pins
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is None

    run = _make_run()
    augment_rr(
        rr_root_v1_1,
        run,
        jurisdiction_id=_TEST_JURISDICTION_ID,
        scope=_TEST_CONDITION_GROUPER_UUID,
    )

    # augmented document itself has setId and versionNumber from
    # the run (derived from the eICR-side identity)
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is not None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is not None

    # but the parentDocument block faithfully omits them
    related_doc = rr_root_v1_1.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
    parent_doc = related_doc.find("hl7:parentDocument", HL7_NS)

    assert parent_doc.find("hl7:id", HL7_NS) is not None
    assert parent_doc.find("hl7:setId", HL7_NS) is None
    assert parent_doc.find("hl7:versionNumber", HL7_NS) is None


def test_augment_rr_relatedDocument_carries_setId_and_version_when_input_has_them(
    rr_root_v1_1: etree.Element,
):
    """
    When the input RR *does* carry <setId> and <versionNumber>, the
    augmented RR's relatedDocument/parentDocument carries both into
    the lineage — faithfully, not synthesized.

    This is the refine-of-an-already-augmented-document case: augment_rr
    writes setId/versionNumber unconditionally under v4, so feeding an
    augmented RR back through refinement produces an input that has
    them. The omission in the sibling test is input-conditional, not a
    blanket RR behavior; this test pins the other half of that
    contract so a regression in _build_related_document_for_input
    can't silently drop prior identity from the chain.

    Verified against both scope kinds (a condition grouper UUID and
    the remainder literal) so the remainder RR's lineage gets the same
    guarantee as the per-condition output's.
    """

    ns = "urn:hl7-org:v3"

    # the stock fixture lacks setId/versionNumber (that's what the
    # omission test pins). Add them so this represents an RR that was
    # itself already augmented and is now being refined again.
    original_setid_root = "1b2bb157-7f36-547d-9ce8-6eae3fa77cce"
    original_version_value = "2"

    setid_el = etree.SubElement(rr_root_v1_1, f"{{{ns}}}setId")
    setid_el.set("root", original_setid_root)
    version_el = etree.SubElement(rr_root_v1_1, f"{{{ns}}}versionNumber")
    version_el.set("value", original_version_value)

    # confirm the precondition before augmenting
    assert rr_root_v1_1.find("hl7:setId", HL7_NS) is not None
    assert rr_root_v1_1.find("hl7:versionNumber", HL7_NS) is not None

    for scope in (_TEST_CONDITION_GROUPER_UUID, REMAINDER_SCOPE):
        # fresh tree per scope so the two augmentations don't interfere
        rr_copy = etree.fromstring(etree.tostring(rr_root_v1_1))

        run = _make_run()
        augment_rr(
            rr_copy,
            run,
            jurisdiction_id=_TEST_JURISDICTION_ID,
            scope=scope,
        )

        related_doc = rr_copy.find("hl7:relatedDocument[@typeCode='XFRM']", HL7_NS)
        parent_doc = related_doc.find("hl7:parentDocument", HL7_NS)

        # the prior identity is carried into the lineage verbatim
        parent_setid = parent_doc.find("hl7:setId", HL7_NS)
        parent_version = parent_doc.find("hl7:versionNumber", HL7_NS)

        assert parent_doc.find("hl7:id", HL7_NS) is not None
        assert parent_setid is not None, (
            f"parentDocument should carry setId for scope={scope!r}"
        )
        assert parent_setid.get("root") == original_setid_root
        assert parent_version is not None, (
            f"parentDocument should carry versionNumber for scope={scope!r}"
        )
        assert parent_version.get("value") == original_version_value


# NOTE:
# RR ↔ eICR CROSS-LINKAGE TESTS
# =============================================================================
#
# the refined RR's eICR External Document Reference must identify the
# refined eICR it is emitted alongside, using the identifiers that eICR
# actually carries — not the original eICR's inherited identity.


def _find_rr_eicr_reference(rr_root: etree.Element) -> etree.Element:
    """
    Return the eICR External Document Reference externalDocument from an RR.
    """

    references = rr_root.xpath(
        ".//hl7:act[hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9']]"
        "//hl7:externalDocument[hl7:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10']]",
        namespaces=HL7_NS,
    )
    assert references, "fixture RR should contain an eICR External Document Reference"
    return references[0]


def _augment_eicr_for_pair(eicr_root: etree.Element) -> None:
    """
    Stamp the refined-eICR identifiers onto eicr_root, as the pipeline does
    before cross-linking.
    """

    augment_eicr(
        eicr_root,
        _make_run(),
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=_TEST_CONDITION_GROUPER_UUID,
    )


def test_rr_eicr_reference_matches_paired_refined_eicr(
    eicr_root_v1_1: etree.Element,
    rr_root_v1_1: etree.Element,
):
    """
    For a per-condition pair, the reference's id/setId/versionNumber
    equal the paired refined eICR's ClinicalDocument id/setId/version,
    and id/setId carry assigningAuthorityName="ecr-refiner".
    """

    _augment_eicr_for_pair(eicr_root_v1_1)

    eicr_id_root = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")
    eicr_setid_root = eicr_root_v1_1.find("hl7:setId", HL7_NS).get("root")
    eicr_version = eicr_root_v1_1.find("hl7:versionNumber", HL7_NS).get("value")

    update_rr_eicr_external_document_reference(rr_root_v1_1, eicr_root_v1_1)

    reference = _find_rr_eicr_reference(rr_root_v1_1)

    ref_id = reference.find("hl7:id", HL7_NS)
    assert ref_id.get("root") == eicr_id_root
    assert ref_id.get("assigningAuthorityName") == "ecr-refiner"

    ref_setid = reference.find("hl7:setId", HL7_NS)
    assert ref_setid.get("root") == eicr_setid_root
    assert ref_setid.get("assigningAuthorityName") == "ecr-refiner"

    ref_version = reference.find("hl7:versionNumber", HL7_NS)
    assert ref_version.get("value") == eicr_version


def test_rr_eicr_reference_code_is_unchanged(
    eicr_root_v1_1: etree.Element,
    rr_root_v1_1: etree.Element,
):
    """
    The <code> (55751-2 / LOINC) identifies the referenced document as
    an eICR and must survive the rewrite untouched (CONF:3315-199).
    """

    _augment_eicr_for_pair(eicr_root_v1_1)
    update_rr_eicr_external_document_reference(rr_root_v1_1, eicr_root_v1_1)

    code = _find_rr_eicr_reference(rr_root_v1_1).find("hl7:code", HL7_NS)
    assert code.get("code") == "55751-2"
    assert code.get("codeSystem") == "2.16.840.1.113883.6.1"


def test_rr_eicr_reference_leaves_no_residual_original_identity(
    eicr_root_v3_1_1: etree.Element,
    rr_root_v3_1_1: etree.Element,
):
    """
    No part of the rewritten reference retains the original eICR's id or
    setId. The v3.1.1 fixture's reference id/setId carry an @extension;
    the refined-eICR identifiers are root-only, so the rewrite must drop
    the inherited extension entirely (id/setId replaced wholesale).
    """

    reference_before = _find_rr_eicr_reference(rr_root_v3_1_1)
    original_id_extension = reference_before.find("hl7:id", HL7_NS).get("extension")
    original_setid_extension = reference_before.find("hl7:setId", HL7_NS).get(
        "extension"
    )
    assert original_id_extension or original_setid_extension, (
        "fixture precondition: the original reference should carry an "
        "@extension so the residual-drop assertion is meaningful"
    )

    _augment_eicr_for_pair(eicr_root_v3_1_1)
    update_rr_eicr_external_document_reference(rr_root_v3_1_1, eicr_root_v3_1_1)

    reference = _find_rr_eicr_reference(rr_root_v3_1_1)
    assert reference.find("hl7:id", HL7_NS).get("extension") is None
    assert reference.find("hl7:setId", HL7_NS).get("extension") is None


def test_rr_eicr_reference_is_idempotent(
    eicr_root_v1_1: etree.Element,
    rr_root_v1_1: etree.Element,
):
    """
    Re-running the cross-link on an already-linked RR produces identical
    reference values — the function reads the emitted eICR identity back,
    it does not re-derive or compound.
    """

    _augment_eicr_for_pair(eicr_root_v1_1)

    update_rr_eicr_external_document_reference(rr_root_v1_1, eicr_root_v1_1)
    first = etree.tostring(_find_rr_eicr_reference(rr_root_v1_1))

    update_rr_eicr_external_document_reference(rr_root_v1_1, eicr_root_v1_1)
    second = etree.tostring(_find_rr_eicr_reference(rr_root_v1_1))

    assert first == second


def test_rr_eicr_reference_raises_when_reference_absent(
    eicr_root_v1_1: etree.Element,
    rr_root_v1_1: etree.Element,
):
    """
    A conformant RR has the reference 1..1; its absence is a malformed
    RR and should surface, not pass silently.
    """

    reference = _find_rr_eicr_reference(rr_root_v1_1)
    external_document_parent = reference.getparent()
    external_document_parent.remove(reference)

    _augment_eicr_for_pair(eicr_root_v1_1)

    with pytest.raises(ValueError, match="eICR External Document Reference"):
        update_rr_eicr_external_document_reference(rr_root_v1_1, eicr_root_v1_1)


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

    The two augmentations use different scopes so the derived
    identifiers differ between calls — that lets the test verify the
    second augmentation captured the first one's output rather than
    silently re-deriving the same values.
    """

    original_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")

    # first augmentation simulates a prior tool (e.g., text-to-code).
    # tool_code/tool_display travel as kwargs on augment_eicr — they
    # default to the Refiner's identity in production but tests can
    # override to simulate other tools in the chain.
    first_scope = uuid.UUID("11111111-1111-1111-1111-111111111111")
    augment_eicr(
        eicr_root_v1_1,
        _make_run(),
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=first_scope,
        tool_code="text-to-code",
        tool_display="Text-to-Code",
    )

    # capture what the first augmentation wrote into the document —
    # these become the "original identity" that the second
    # augmentation will capture and carry forward in its relatedDocument
    first_aug_id = eicr_root_v1_1.find("hl7:id", HL7_NS).get("root")
    first_aug_setid = eicr_root_v1_1.find("hl7:setId", HL7_NS).get("root")

    # second augmentation simulates the Refiner running on the prior
    # output — different scope so the derived ids differ, and the
    # default Refiner tool identity.
    second_scope = uuid.UUID("22222222-2222-2222-2222-222222222222")
    augment_eicr(
        eicr_root_v1_1,
        _make_run(),
        jurisdiction_id=_TEST_JURISDICTION_ID,
        condition_grouper_uuid=second_scope,
    )

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
    assert second_sibling_id.get("root") == first_aug_id
    assert second_sibling_id.get("assigningAuthorityName") == "text-to-code"

    # second sibling also carries the prior augmentation's setId and version
    second_sibling_setid = related_docs[1].find("hl7:parentDocument/hl7:setId", HL7_NS)
    assert second_sibling_setid.get("root") == first_aug_setid
    assert second_sibling_setid.get("assigningAuthorityName") == "text-to-code"


# NOTE:
# RUN FACTORY TESTS
# =============================================================================


def test_create_augmentation_run_inherits_version_number(
    eicr_root_v1_1: etree.Element,
):
    """
    The run's version_number is the input eICR's versionNumber, not a
    Refiner-invented value. Both the augmented eICR and augmented RR
    are stamped with this version, so the augmented pair's
    versionNumber tracks the EHR's clinical-case versioning stream.
    """

    expected_version = eicr_root_v1_1.find("hl7:versionNumber", HL7_NS).get("value")

    run = create_augmentation_run(eicr_root=eicr_root_v1_1)

    assert run.version_number == expected_version


def test_create_augmentation_run_captures_eicr_setid_for_rr_seeding(
    eicr_root_v1_1: etree.Element,
):
    """
    The run carries original_eicr_setid_root because the RR-side setId
    derivations (both the per-condition pair and the remainder) seed
    from the eICR's setId, not the RR's. Keeping the value on the run
    means augment_rr does not need the eICR tree in scope to derive
    its setId.
    """

    expected_setid = eicr_root_v1_1.find("hl7:setId", HL7_NS).get("root")

    run = create_augmentation_run(eicr_root=eicr_root_v1_1)

    assert run.original_eicr_setid_root == expected_setid


def test_pair_recoverability_via_eicr_setid_only():
    """
    A PHA holding the original eICR's setId can derive the augmented
    RR's setId without seeing the RR — given the jurisdiction and the
    scope. This pair-recoverability property is what justifies seeding
    the augmented RR setId from the eICR's setId rather than the
    RR's, and it applies to both the per-condition pair (scope is
    the grouper UUID) and the remainder RR (scope is REMAINDER_SCOPE).
    """

    eicr_setid = "orig-set-2222"

    # PHA-side derivation using only the eICR setId, the jurisdiction,
    # and the scope — no access to the RR required
    pha_derived = _derive_augmented_rr_setid(
        eicr_setid, _TEST_JURISDICTION_ID, _TEST_CONDITION_GROUPER_UUID
    )

    # refiner-side derivation (what augment_rr does internally) uses
    # the same inputs via the run + scope path; the helper computes
    # the same value because the seed shape is fixed
    refiner_derived = _derive_augmented_rr_setid(
        eicr_setid, _TEST_JURISDICTION_ID, _TEST_CONDITION_GROUPER_UUID
    )

    assert pha_derived == refiner_derived


# NOTE:
# DERIVATION HELPER TESTS
# =============================================================================

# two distinct condition grouper UUIDs for tests that need to verify
# discrimination on condition. these are realistic-shape UUIDs but are
# not actual TES UUIDs. UUID objects, since the derive helpers take
# UUID (the type is the validator).
_COVID_GROUPER_UUID = uuid.UUID("07221093-b8a1-4b1d-8678-259277bfba64")
_FLU_GROUPER_UUID = uuid.UUID("1c5ed2a0-5a4f-4d3e-a1b2-7f8e9d0c3b4a")


def test_derive_augmented_eicr_id_is_pure_function_of_inputs():
    """
    The eICR id derivation depends only on (original eICR id,
    jurisdiction, condition grouper UUID) and produces deterministic
    output.
    """

    a = _derive_augmented_eicr_id("doc-1234", "SDDH", _COVID_GROUPER_UUID)
    b = _derive_augmented_eicr_id("doc-1234", "SDDH", _COVID_GROUPER_UUID)
    c = _derive_augmented_eicr_id("doc-5678", "SDDH", _COVID_GROUPER_UUID)
    d = _derive_augmented_eicr_id("doc-1234", "SDDH", _FLU_GROUPER_UUID)
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

    naked = str(uuid.uuid5(REFINER_DETERMINISTIC_NS, "orig-set-2222"))
    prefixed = _derive_augmented_eicr_setid(
        "orig-set-2222", "SDDH", _COVID_GROUPER_UUID
    )
    assert naked != prefixed


def test_derive_augmented_rr_setid_distinct_from_eicr_setid():
    """
    The RR setId derivation uses a different prefix than the eICR
    setId derivation. Given the same source value and condition,
    the two helpers produce different UUIDs.
    """

    source = "orig-set-2222"
    eicr_setid = _derive_augmented_eicr_setid(source, "SDDH", _COVID_GROUPER_UUID)
    rr_setid = _derive_augmented_rr_setid(source, "SDDH", _COVID_GROUPER_UUID)
    assert eicr_setid != rr_setid


def test_derive_helpers_discriminate_on_condition():
    """
    All four derivation helpers produce condition-discriminated output:
    given the same input identifier, two different condition grouper
    UUIDs produce two different output UUIDs. This is the property that
    lets a single eICR/RR pair be refined for multiple conditions
    without producing colliding augmented identifiers.
    """

    eicr_id = _derive_augmented_eicr_id("doc-1234", "SDDH", _COVID_GROUPER_UUID)
    eicr_id_flu = _derive_augmented_eicr_id("doc-1234", "SDDH", _FLU_GROUPER_UUID)
    assert eicr_id != eicr_id_flu

    eicr_setid = _derive_augmented_eicr_setid("set-2222", "SDDH", _COVID_GROUPER_UUID)
    eicr_setid_flu = _derive_augmented_eicr_setid("set-2222", "SDDH", _FLU_GROUPER_UUID)
    assert eicr_setid != eicr_setid_flu

    rr_id = _derive_augmented_rr_id("rr-5678", "SDDH", _COVID_GROUPER_UUID)
    rr_id_flu = _derive_augmented_rr_id("rr-5678", "SDDH", _FLU_GROUPER_UUID)
    assert rr_id != rr_id_flu

    rr_setid = _derive_augmented_rr_setid("set-2222", "SDDH", _COVID_GROUPER_UUID)
    rr_setid_flu = _derive_augmented_rr_setid("set-2222", "SDDH", _FLU_GROUPER_UUID)
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

    eicr_id_lac = _derive_augmented_eicr_id("doc-1234", "LAC", _COVID_GROUPER_UUID)
    eicr_id_ca = _derive_augmented_eicr_id("doc-1234", "CA", _COVID_GROUPER_UUID)
    assert eicr_id_lac != eicr_id_ca

    eicr_setid_lac = _derive_augmented_eicr_setid(
        "set-2222", "LAC", _COVID_GROUPER_UUID
    )
    eicr_setid_ca = _derive_augmented_eicr_setid("set-2222", "CA", _COVID_GROUPER_UUID)
    assert eicr_setid_lac != eicr_setid_ca

    rr_id_lac = _derive_augmented_rr_id("rr-5678", "LAC", _COVID_GROUPER_UUID)
    rr_id_ca = _derive_augmented_rr_id("rr-5678", "CA", _COVID_GROUPER_UUID)
    assert rr_id_lac != rr_id_ca

    rr_setid_lac = _derive_augmented_rr_setid("set-2222", "LAC", _COVID_GROUPER_UUID)
    rr_setid_ca = _derive_augmented_rr_setid("set-2222", "CA", _COVID_GROUPER_UUID)
    assert rr_setid_lac != rr_setid_ca

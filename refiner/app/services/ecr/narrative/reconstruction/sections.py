from typing import cast

from lxml.etree import _Element

from ...model import HL7_NS
from ...specification.template_oids import (
    IMMUNIZATION_ACTIVITY_V3,
    LABORATORY_RESULT_STATUS_ID,
    PLANNED_IMMUNIZATION_ACTIVITY,
)
from .blocks import Block, DetailRow
from .fields import (
    _GENERIC_COLUMNS,
    _GENERIC_ITEM_COLUMN,
    CONCERN_FIELDS,
    GENERIC_FIELDS,
    IMMUNIZATION_FIELDS,
    MEDICATION_FIELDS,
    PANEL_FIELDS,
    PLANNED_ACT_FIELDS,
    PLANNED_IMMUNIZATION_FIELDS,
    PLANNED_MEDICATION_FIELDS,
    PLANNED_OBSERVATION_FIELDS,
    PLANNED_PROCEDURE_FIELDS,
    PROBLEM_FIELDS,
    RESULT_FIELDS,
    SPECIMEN_FIELDS,
    FieldSpec,
    extract_fields,
)
from .renderers import render_code_display, render_entry_concept

# NOTE:
# LAYER 3 — PER-SECTION JOINS (the part kept as code)
# =============================================================================


def reconstruct_results(section: _Element) -> list[Block]:
    """
    Reconstruct the Results section as one block per panel.

    JOIN section: each organizer is a self-contained block. Its context is
    the PANEL (its own fields) merged with the SPECIMEN reached SIDEWAYS to a
    sibling procedure; its detail rows are the child result observations.
    Context is rendered once per block — never repeated down the result rows.

    Args:
        section: The post-prune, post-enrich Results <section>.

    Returns:
        One Block per organizer that has surviving result observations.
    """

    blocks: list[Block] = []

    for organizer in section.findall("hl7:entry/hl7:organizer", HL7_NS):
        context = extract_fields(organizer, PANEL_FIELDS)
        # the DISPLAY half only: the context table one row up already carries
        # the qualified concept, and repeating "(LOINC 105066-5)" in the
        # caption directly above it is noise
        panel_name = render_code_display(organizer.find("hl7:code", HL7_NS))

        procedure = organizer.find("hl7:component/hl7:procedure", HL7_NS)
        context |= (
            extract_fields(procedure, SPECIMEN_FIELDS)
            if procedure is not None
            else {spec.label: "" for spec in SPECIMEN_FIELDS}
        )

        # an organizer/component may hold a Laboratory Result Status (...4.418),
        # which IS an <observation> and which the shared-context prune carve-out
        # deliberately keeps alive. unfiltered it renders as a result row
        # reading "Lab order result status"; it belongs in the block context
        # (PANEL_FIELDS), not the table
        #
        # this **excludes** the known non-result template rather than **requiring**
        # the Result Observation V3 one, and the direction is deliberate. requiring
        # ...4.2 would blank the whole table for any sender that omits the
        # templateId — turning the DRIV assertion ("narrative is clinically
        # equivalent to the structured entries") into a lie, which is a far
        # worse outcome than one spurious row. the prune guard in
        # entry_match_rules is inclusive for the mirror-image reason: there,
        # "no result templateId" means **retain** as context, so erring toward the
        # template keeps more. here it would show less
        result_observations = cast(
            list[_Element],
            organizer.xpath(
                "hl7:component/hl7:observation"
                f"[not(hl7:templateId[@root='{LABORATORY_RESULT_STATUS_ID}'])]",
                namespaces=HL7_NS,
            ),
        )
        rows = [
            DetailRow(source=obs, values=extract_fields(obs, RESULT_FIELDS))
            for obs in result_observations
        ]
        if rows:
            blocks.append(
                Block(
                    context=context,
                    columns=[spec.label for spec in RESULT_FIELDS],
                    rows=rows,
                    # names the battery these rows belong to. a panel whose
                    # code resolves to nothing still gets a caption -- it is
                    # what marks the table as subordinate to the one above it
                    # -- but a standalone one, not a dangling
                    # "Tests in panel: " with the name missing
                    caption=(
                        f"Tests in panel: {panel_name}"
                        if panel_name
                        else "Tests in this panel"
                    ),
                )
            )

    return blocks


def reconstruct_problems(section: _Element) -> list[Block]:
    """
    Reconstruct the Problems section as one block per concern.

    JOIN section, mirroring Results one level down: each Problem Concern Act
    is a self-contained block whose context is the concern (status + noted
    date) and whose detail rows are the Problem Observations reached DOWN
    through entryRelationship. Context renders once per block, not per row.

    Args:
        section: The post-prune, post-enrich Problems <section>.

    Returns:
        One Block per concern act that has surviving problem observations.
    """

    blocks: list[Block] = []

    for act in section.findall("hl7:entry/hl7:act", HL7_NS):
        context = extract_fields(act, CONCERN_FIELDS)

        # only the Problem Observation is a problem row. a Problem Concern Act
        # also permits entryRelationship[@typeCode='REFR'] carrying a Priority
        # Preference (...22.4.143), itself an <observation>; unfiltered it renders
        # as a phantom problem row. the Problem Observation SHALL sit under
        # typeCode='SUBJ' (CONF:1198-9035), so require it
        #
        # - this requires the expected discriminator, the opposite of the Results
        # row filter's exclude-the-known-noise stance--and deliberately.
        # - there the discriminator is a templateId senders frequently omit, so
        # requiring it would blank the table (a DRIV lie)
        # - here it is a positional SHALL conformant senders reliably emit,
        # so requiring it drops the noise without that risk
        rows = [
            DetailRow(source=obs, values=extract_fields(obs, PROBLEM_FIELDS))
            for obs in act.findall(
                "hl7:entryRelationship[@typeCode='SUBJ']/hl7:observation", HL7_NS
            )
        ]
        if rows:
            blocks.append(
                Block(
                    context=context,
                    columns=[spec.label for spec in PROBLEM_FIELDS],
                    rows=rows,
                )
            )

    return blocks


def _reconstruct_flat(
    section: _Element,
    *,
    anchor_xpath: str,
    fields: list[FieldSpec],
) -> list[Block]:
    """
    Reconstruct a FLAT section as a single context-free table.

    The row IS the anchor entry; there is nothing to reach up or sideways
    for. Every anchor becomes one row in a single block with empty context
    (the assembler renders no context table for it). This is the shape both
    substanceAdministration sections (Immunizations, Medications) take.

    Args:
        section: The post-prune, post-enrich <section>.
        anchor_xpath: Row anchor, relative to the section.
        fields: The field map read off each anchor.

    Returns:
        A single Block, or [] when no anchor survived.
    """

    rows = [
        DetailRow(
            source=anchor,
            values=extract_fields(anchor, fields),
            negated=anchor.get("negationInd") == "true",
        )
        for anchor in section.findall(anchor_xpath, HL7_NS)
    ]
    if not rows:
        return []

    return [Block(context={}, columns=[spec.label for spec in fields], rows=rows)]


def reconstruct_immunizations(section: _Element) -> list[Block]:
    """
    Reconstruct the Immunizations section: one row per vaccine.

    Args:
        section: The post-prune, post-enrich Immunizations <section>.

    Returns:
        A single flat Block, or [] when no substanceAdministration survived.
    """

    return _reconstruct_flat(
        section,
        anchor_xpath="hl7:entry/hl7:substanceAdministration",
        fields=IMMUNIZATION_FIELDS,
    )


def reconstruct_medications(section: _Element) -> list[Block]:
    """
    Reconstruct the Medications Administered section: one row per medication.

    Args:
        section: The post-prune, post-enrich Medications <section>.

    Returns:
        A single flat Block, or [] when no substanceAdministration survived.
    """

    return _reconstruct_flat(
        section,
        anchor_xpath="hl7:entry/hl7:substanceAdministration",
        fields=MEDICATION_FIELDS,
    )


# NOTE:
# PLAN OF TREATMENT — the heterogeneous section
# =============================================================================
# every other reconstructable section is **one** kind of thing repeated. plan of
# treatment is five: planned observations, procedures, acts, medications and
# immunizations sit as siblings under a single <section>. that is why it emits
# one **captioned** block per entry kind instead of one block per grouping entry:
# the kinds do not share columns, and "unlike patterns are never collapsed into
# a shared grid" cuts the other way here--without a caption the reader gets a
# run of unlabelled tables
#
# the split is by ELEMENT NAME, except for substanceAdministration, which is
# both the medication and the immunization shape and can only be told apart by
# templateId. that mirrors how the matching rules for this section already
# discriminate (see specification/entry_match_rules.py, rules 2-5), so the two
# halves of the pipeline agree on what an entry **is**

# a substanceAdministration bearing either immunization template is a vaccine;
# the Planned variant (22.4.120) is IG-recommended for this section and the
# event-mood one (22.4.52) is the discouraged-but-permitted fallback the
# matching rules also accept
_IMMUNIZATION_TEMPLATES: tuple[str, ...] = (
    PLANNED_IMMUNIZATION_ACTIVITY,
    IMMUNIZATION_ACTIVITY_V3,
)


def _is_planned_immunization(anchor: _Element) -> bool:
    """
    Return True if a `<substanceAdministration>` is a vaccine, not a drug.
    """

    return any(
        template.get("root") in _IMMUNIZATION_TEMPLATES
        for template in anchor.findall("hl7:templateId", HL7_NS)
    )


def _entry_kind_block(
    anchors: list[_Element],
    *,
    fields: list[FieldSpec],
    caption: str,
) -> Block:
    """
    Build the captioned block for one Plan of Treatment entry kind.

    The caller skips empty kinds before calling, so this always builds a
    block (one row per anchor).
    """

    return Block(
        context={},
        columns=[spec.label for spec in fields],
        rows=[
            DetailRow(
                source=anchor,
                values=extract_fields(anchor, fields),
                negated=anchor.get("negationInd") == "true",
            )
            for anchor in anchors
        ],
        caption=caption,
    )


def reconstruct_plan_of_treatment(section: _Element) -> list[Block]:
    """
    Reconstruct the Plan of Treatment section as one block per entry kind.

    HETEROGENEOUS section: entries are grouped by the clinical statement
    they are, each kind rendering as its own captioned table with its own
    columns. Blocks come out in the spreadsheet's order (observation,
    procedure, act, medication, immunization) rather than document order,
    so like sits with like.

    Args:
        section: The post-prune, post-enrich Plan of Treatment <section>.

    Returns:
        One Block per entry kind that has surviving entries.
    """

    # a substanceAdministration carrying **neither** immunization template is read
    # as a medication rather than dropped: its field map is the generic
    # substanceAdministration shape, and an entry that survived pruning with no
    # narrative row would make the section's typeCode="DRIV" a lie
    immunizations: list[_Element] = []
    medications: list[_Element] = []
    for anchor in section.findall("hl7:entry/hl7:substanceAdministration", HL7_NS):
        target = immunizations if _is_planned_immunization(anchor) else medications
        target.append(anchor)

    # (anchors, field map, caption) per entry kind, in spreadsheet order. the
    # grouping is by element name, except substanceAdministration — one element
    # serving two kinds — which was split by templateId above
    kinds: list[tuple[list[_Element], list[FieldSpec], str]] = [
        (
            section.findall("hl7:entry/hl7:observation", HL7_NS),
            PLANNED_OBSERVATION_FIELDS,
            "Planned Observations",
        ),
        (
            section.findall("hl7:entry/hl7:procedure", HL7_NS),
            PLANNED_PROCEDURE_FIELDS,
            "Planned Procedures",
        ),
        (
            section.findall("hl7:entry/hl7:act", HL7_NS),
            PLANNED_ACT_FIELDS,
            "Planned Activities",
        ),
        (medications, PLANNED_MEDICATION_FIELDS, "Planned Medications"),
        (immunizations, PLANNED_IMMUNIZATION_FIELDS, "Planned Immunizations"),
    ]

    # a kind with no surviving entries contributes no table
    return [
        _entry_kind_block(anchors, fields=fields, caption=caption)
        for anchors, fields, caption in kinds
        if anchors
    ]


# NOTE:
# LAYER 3 — THE GENERIC FALLBACK
# =============================================================================
# a per-section reconstructor knows one shape. It anchors on the arrangement
# the IG describes -- Results on `entry/organizer`, Problems on `entry/act` --
# and an entry arranged differently produces no row, even though it matched
# and survived pruning. That is not hypothetical: a Problem Observation under a
# non-SUBJ entryRelationship, or a Result Observation sitting directly under
# `<entry>` with no organizer, both match, both survive, and both render
# nothing.
#
# Silently is the problem. The section still reports "reconstructed", every
# surviving entry is still stamped typeCode="DRIV" -- the document asserting
# its narrative is derived from and clinically equivalent to those entries --
# and one of them is missing from the narrative entirely. The assertion
# becomes false and nothing says so.
#
# So the fallback is not a separate path taken when reconstruction "fails". It
# runs after every reconstruction, over whatever entries the section's own
# reconstructor did not represent, and renders them in reduced form: the
# concept, when it happened, its status. Enough for a reviewer to see that
# something is there and what it is. The block is captioned, and the section's
# provenance footnote reports that it happened, so a narrative that looks thin
# says why rather than leaving the reader to wonder.

_GENERIC_CAPTION: str = (
    "Additional entries — shown in reduced form; "
    "full reconstruction unavailable for this structure"
)


def _entry_statement(entry: _Element) -> _Element | None:
    """
    Return the clinical statement an `<entry>` wraps, or None if it wraps none.
    """

    return next((child for child in entry if isinstance(child.tag, str)), None)


def _unrepresented_statements(section: _Element, blocks: list[Block]) -> list[_Element]:
    """
    Return the clinical statements no reconstructed row already covers.

    Identity is compared by tree path rather than by object: lxml builds
    element proxies on demand, so two lookups of the same node can hand back
    different Python objects and `id()`/`is` are not dependable across them.
    `getpath` is derived from the node's position, so it is stable.

    An entry counts as represented when a row's source is the entry's own
    statement OR anything beneath it -- the join sections anchor their rows on
    child observations, not on the entry.

    Args:
        section: The post-prune section.
        blocks: The blocks the section's own reconstructor produced.

    Returns:
        One statement element per unrepresented entry, in document order.
    """

    tree = section.getroottree()
    represented = {tree.getpath(row.source) for block in blocks for row in block.rows}

    unrepresented: list[_Element] = []
    for entry in section.findall("hl7:entry", HL7_NS):
        statement = _entry_statement(entry)
        if statement is None:
            continue
        prefix = tree.getpath(entry) + "/"
        if any(path.startswith(prefix) for path in represented):
            continue
        unrepresented.append(statement)
    return unrepresented


def _generic_block(statements: list[_Element]) -> Block:
    """
    Build the captioned reduced-form block for unrepresented statements.
    """

    rows = [
        DetailRow(
            source=statement,
            values={_GENERIC_ITEM_COLUMN: render_entry_concept(statement)}
            | extract_fields(statement, GENERIC_FIELDS),
            negated=statement.get("negationInd") == "true",
        )
        for statement in statements
    ]
    return Block(
        context={},
        columns=_GENERIC_COLUMNS,
        rows=rows,
        caption=_GENERIC_CAPTION,
    )

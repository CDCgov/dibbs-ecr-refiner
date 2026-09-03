from app.services.ecr.narrative.identifiers import compact_reconstruction_references


class TestCompactReconstructionReferences:
    """
    The minted entry→narrative reference pointer is a mixed-content
    <reference> and must serialize without surrounding whitespace
    (Boone, The CDA Book, ch. 6). Pretty-printing the whole document
    indents it; this collapses it back, scoped to refiner-minted ids.
    """

    def test_collapses_pretty_printed_reference(self):
        # the shape pretty_print produces over the whole tree
        pretty = (
            "<observation>\n"
            "  <text>\n"
            '    <reference value="#ecr-refiner-30954-2-20260101000000-row1"/>\n'
            "  </text>\n"
            "</observation>\n"
        )
        result = compact_reconstruction_references(pretty)
        assert (
            '<text><reference value="#ecr-refiner-30954-2-20260101000000-row1"/></text>'
            in result
        )
        # no whitespace survives between <text>/<reference>/</text>
        assert "<text>\n" not in result
        assert "/>\n  </text>" not in result

    def test_leaves_author_attested_references_untouched(self):
        # a source-document narrative reference (not refiner-minted) is
        # outside our remit — its whitespace is preserved
        pretty = (
            "<observation>\n"
            "  <text>\n"
            '    <reference value="#Result.1.2.840.Comp1"/>\n'
            "  </text>\n"
            "</observation>\n"
        )
        assert compact_reconstruction_references(pretty) == pretty

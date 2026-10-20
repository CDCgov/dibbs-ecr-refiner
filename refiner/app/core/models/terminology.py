from dataclasses import dataclass

# NOTE:
# the three code shapes this codebase actually needs, side by side on purpose. before
# this file they were `CodedConcept`, `DbCode` and `Coding` -- two of which named FHIR
# types they did not match, and one of which was the union of three queries' `SELECT`
# lists. a reader could not tell them apart, which is how a code lost its system on the
# way to S3 (#967) and how an OID-scoped section stopped matching custom codes.
#
# they live in `core` because every layer reads them: `db/` nests them inside its frozen
# rows, `services/` builds them from those rows, `api/` ships them to a browser, and
# `services/ecr/` matches on them with no database in reach. a home under `services/`
# would make `db/` import from `services/` to type its own rows; a home under `db/`
# would make the refinement core import the database layer, which
# `tests/unit/test_layering.py` forbids


@dataclass(frozen=True)
class CodeLabel:
    """
    A code and the label to render for it, with **no code system**.

    Safe only where the surrounding structure establishes the system -- a condition's
    RSG codes are SNOMED by construction, for instance. It is deliberately _not_
    enough to match on: a code without a system is not resolvable, and the name is
    chosen to read wrong in matching code. Use `Coding` there.
    """

    code: str
    display_name: str


@dataclass(frozen=True)
class Coding:
    """
    A code, its label, and the system that scopes it.

    The unit the refinement pipeline matches on: enough context to resolve a code
    (`code` + `system_oid`) and to enrich the document with a label
    (`display_name`).

    Keeps the FHIR-ish name deliberately. ADR 0016 rule 1 is "one name per concept",
    and this shape is a narrow subset of FHIR `Coding` -- `{system, version, code,
    display, userSelected}` with the optional fields dropped and `system` carried as
    an OID. The one real divergence is that `system_oid` holds the literal `"Other"`
    for custom codes with no standard system, which is a **routing key** rather than
    an identifier; see `OID_TO_SYSTEM_KEY_MAP`. That is a data question, not a naming
    one, and no rename fixes it.
    """

    code: str
    display_name: str
    system_oid: str


@dataclass(frozen=True)
class CodeExportRow:
    """
    One row of a code CSV export: a code, its label, and its system's label.

    The TES diff writer takes the condition name from the enclosing `DbConditionDiff`
    rather than the row, so it is not a field here. The system is a **label** and not an
    OID because these rows are read by a person in a spreadsheet, never matched
    against a document -- `Coding` is the shape for that.
    """

    code: str
    display_name: str
    system_display_name: str

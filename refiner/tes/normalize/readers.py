"""
Per-release readers for TES FHIR ValueSet bundles.

TES has changed the shape of its published artifacts several times. Rather than
branching on version inside a single generic parser, each shape gets its own
reader, and a release is mapped to the reader that understands it. The reader
names and their docstrings are the record of what TES changed and when.

Adding support for a new TES shape means writing a new reader and giving it a
segment in `SCHEMA_ERAS` -- not editing an existing one. Old readers stay
correct for the releases they were written for, because those files never
change once published.

## What has changed, release by release

Three independent shape changes, at three different releases. Every number below
is measured from the committed bundles rather than assumed, and
`tes/verify/processed.py` asserts them, so the next change fails loudly instead of
silently reading the wrong field.

| Release                 | Leaf codes live in            | `expansion` | `concept[]` optional |
| ----------------------- | ----------------------------- | ----------- | -------------------- |
| 1.0.0 - 3.0.0           | `compose.include[].concept`   | absent      | no                   |
| RSG 20241008 - 20250829 | `compose.include[].concept`   | absent      | no                   |
| 4.0.0 - 6.0.0           | `compose.include[].concept`   | redundant   | no                   |
| RSG 20260327            | `compose.include[].concept`   | redundant   | no                   |
| 7.0.0 +                 | **`expansion.contains`**      | needed      | **yes** (191 of 220) |
| RSG 20260731            | `expansion.contains`          | needed      | not yet exercised    |

* **4.0.0** added `expansion.contains` to every kind of grouper, condition
  groupers included -- they are otherwise pure manifests, and nothing reads
  their expansion, because a condition's codes come from resolving its children.
* **7.0.0** is where `concept[]` became optional: 191 of 220 additional context
  groupers dropped it. That is what forces the reader split. Before 7.0.0 the
  authored `concept[]` is always present; from 7.0.0 it may not be. Where both
  exist the expansion is a superset in every published case, so reading the
  expansion from 7.0.0 onward loses nothing.
* The RSG datetime family has not yet shipped a grouper without `concept[]`, but
  it crossed the same expansion boundary at 20260327 and reads with the same
  reader, so it is treated as the same era.

Two facts worth holding onto, because they are easy to get wrong:

* `compose.include[].concept[]` entries are `ValueSetComposeIncludeConcept`,
  which has **no `system`** -- the system lives on the enclosing `include`.
  `expansion.contains[]` entries are `ValueSetExpansionContains`, which carry
  their own `system`. Neither is a `Coding`.
* TES publishes two version families: semver (`7.0.0`) on condition and
  additional context groupers, and datetimes (`20260731`) on reporting
  specification groupers. A release is one or the other, never both.
"""

import re
from collections.abc import Callable
from enum import StrEnum

from .model import FhirCodeInfo, ValueSetDict

SEMVER_PATTERN = re.compile(r"\d+\.\d+\.\d+")
DATETIME_PATTERN = re.compile(r"\d{8}")


class SchemaEra(StrEnum):
    """
    The distinct artifact shapes TES has published.
    """

    CONCEPT_LIST = "concept_list"
    EXPANSION = "expansion"


class UnknownReleaseError(ValueError):
    """
    Raised when a ValueSet's version matches no known version family.
    """


def _release_key(version: str) -> tuple[str, tuple[int, ...] | str]:
    """
    Resolve a version string to a value comparable within its own family.

    Returns a ("semver", tuple) or ("datetime", str) pair so callers compare
    like with like. TES publishes one family or the other, never both, so a
    version matching neither means a numbering scheme this module predates.

    Args:
        version: The `ValueSet.version` value, e.g. "7.0.0" or "20260731".

    Returns:
        The family name and a key comparable against that family's boundaries.

    Raises:
        UnknownReleaseError: The version matches neither family.
    """

    if match := SEMVER_PATTERN.search(version):
        return ("semver", tuple(int(part) for part in match.group(0).split(".")))
    if match := DATETIME_PATTERN.search(version):
        return ("datetime", match.group(0))

    raise UnknownReleaseError(
        f"TES version {version!r} matches neither the semver nor the datetime "
        "version family. A new reader and SCHEMA_ERAS entry are needed."
    )


def era_for_version(version: str) -> SchemaEra:
    """
    Map a TES version string to the artifact shape it uses.

    This is the complement of `leaf_may_omit_concepts`: the expansion reader is
    needed exactly when `concept[]` stopped being guaranteed. Deriving it rather
    than encoding the boundary twice keeps the two from drifting -- they used to
    disagree for any release between 6.0.0 and 7.0.0.

    Args:
        version: The `ValueSet.version` value, e.g. "7.0.0" or "20260731".

    Returns:
        The SchemaEra whose reader understands this release.

    Raises:
        UnknownReleaseError: The version matches neither version family.
    """

    return (
        SchemaEra.EXPANSION
        if leaf_may_omit_concepts(version)
        else SchemaEra.CONCEPT_LIST
    )


def read_codes_concept_list(
    valueset: ValueSetDict, source_name: str
) -> set[FhirCodeInfo]:
    """
    Read codes from a pre-7.0.0 leaf grouper.

    Codes are authored in `compose.include[].concept[]`. The system is carried
    on the enclosing `include`, so it has to be pushed down onto each concept --
    `ValueSetComposeIncludeConcept` has no system of its own.

    Args:
        valueset: The raw ValueSet resource.
        source_name: Pre-computed display name for the grouper.

    Returns:
        Every (system, code, display) this grouper declares.
    """

    source_url = valueset.get("url")
    compose = valueset.get("compose")
    if not source_url or not compose:
        return set()

    return {
        FhirCodeInfo(
            system_url=system,
            code=concept["code"],
            display=concept.get("display"),
            source_url=source_url,
            source_name=source_name,
        )
        for include in compose.get("include", [])
        if (system := include.get("system"))
        for concept in include.get("concept", []) or []
        if concept.get("code")
    }


def read_codes_expansion(valueset: ValueSetDict, source_name: str) -> set[FhirCodeInfo]:
    """
    Read codes from a 7.0.0-or-later leaf grouper.

    Codes moved to `expansion.contains[]`, where each `ValueSetExpansionContains`
    carries its own system. Groupers in this era may also still declare a
    `compose.include[].concept[]`, but the expansion is a superset of it in every
    published case, and 191 of the 501 groupers in 7.0.0 have no `concept[]` at
    all -- so the expansion is the only correct source for this era.

    Args:
        valueset: The raw ValueSet resource.
        source_name: Pre-computed display name for the grouper.

    Returns:
        Every (system, code, display) this grouper expands to.
    """

    source_url = valueset.get("url")
    expansion = valueset.get("expansion")
    if not source_url or not expansion:
        return set()

    return {
        FhirCodeInfo(
            system_url=system,
            code=entry["code"],
            display=entry.get("display"),
            source_url=source_url,
            source_name=source_name,
        )
        for entry in expansion.get("contains", [])
        if (system := entry.get("system")) and entry.get("code")
    }


type CodeReader = Callable[[ValueSetDict, str], set[FhirCodeInfo]]

SCHEMA_ERAS: dict[SchemaEra, CodeReader] = {
    SchemaEra.CONCEPT_LIST: read_codes_concept_list,
    SchemaEra.EXPANSION: read_codes_expansion,
}

# when `expansion.contains` first appeared on every kind of grouper, condition
# groupers included. Absent before this, present from it
FIRST_SEMVER_WITH_EXPANSION = (4, 0, 0)
FIRST_DATETIME_WITH_EXPANSION = "20260327"

# when a leaf grouper was first allowed to publish no `compose.include[].concept`
# at all. This is the boundary the readers split on
FIRST_SEMVER_OMITTING_CONCEPTS = (7, 0, 0)
FIRST_DATETIME_OMITTING_CONCEPTS = "20260731"


def release_has_expansion(version: str) -> bool:
    """
    Whether every grouper in this release carries `expansion.contains`.
    """

    family, key = _release_key(version)
    boundary = (
        FIRST_SEMVER_WITH_EXPANSION
        if family == "semver"
        else FIRST_DATETIME_WITH_EXPANSION
    )
    return key >= boundary


def leaf_may_omit_concepts(version: str) -> bool:
    """
    Whether a leaf grouper in this release may publish no `concept[]`.

    This is the boundary the readers split on: below it the authored `concept[]`
    is always present, at or above it the expansion is the only reliable source.
    """

    family, key = _release_key(version)
    boundary = (
        FIRST_SEMVER_OMITTING_CONCEPTS
        if family == "semver"
        else FIRST_DATETIME_OMITTING_CONCEPTS
    )
    return key >= boundary


def reader_for_version(version: str) -> CodeReader:
    """
    Return the code reader that understands a given TES release.

    Args:
        version: The `ValueSet.version` value.

    Returns:
        The reader function for that release's artifact shape.
    """

    return SCHEMA_ERAS[era_for_version(version)]

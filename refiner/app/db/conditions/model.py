from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.models.terminology import CodeLabel
from app.db.codes.model import DbConditionCode


@dataclass(frozen=True)
class DbConditionsContextGrouper:
    """
    Model for a condition context grouper row in the database.
    """

    id: UUID
    condition_id: UUID
    display_name: str
    category: str
    canonical_url: str
    code_count: int
    completeness: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DbConditionBase:
    """
    Simple information about a condition from the database. Excludes info about code sets.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
    coverage_level: str | None = None


@dataclass(frozen=True)
class DbCondition(DbConditionBase):
    """
    Model to represent a complete condition row from the database (row).

    This represents the full structure of the conditions table, including
    all the JSON fields that contain aggregated codes from child RSGs.
    """

    # the child RSG codes that match 1:1 with RC SNOMED codes
    # that will come **from** the RR's coded information organizer
    child_rsg_snomed_codes: list[str] = field(default_factory=list)
    # jsonb columns storing code/display pairs
    # this data is extracted from flat files from the TES
    # and seeded from CG's RSG and ACG children
    # coverage level from the crmi-curationCoverageLevel extension
    # on the condition grouper ValueSet; null when the extension is not present
    codes: list[DbConditionCode] = field(default_factory=list)
    coverage_level_reason: str | None = None
    coverage_level_date: datetime | None = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "DbCondition":
        """
        Transforms a dictionary object into a DbCondition.

        Args:
            row (dict[str, Any]): Dictionary containing condition data from the database.

        Returns:
            DbCondition: The condition object
        """
        return cls(
            id=row["id"],
            display_name=row["display_name"],
            canonical_url=row["canonical_url"],
            version=row["version"],
            # NOTE:
            # `JSONB_BUILD_OBJECT` renders a uuid as a JSON string, so `system_id`
            # arrives as `str` and the annotation says `UUID`. this used to differ
            # from the `class_row` path, where it was a real `UUID` -- a
            # `dict[UUID, ...]` lookup on this one missed every key. that other path
            # is gone now; the cast stays because the annotation has to be true
            codes=[
                DbConditionCode(**{**c, "system_id": UUID(c["system_id"])})
                for c in row["codes"]
            ],
            child_rsg_snomed_codes=row.get("child_rsg_snomed_codes") or [],
            coverage_level=row.get("coverage_level"),
            coverage_level_reason=row.get("coverage_level_reason"),
            coverage_level_date=row.get("coverage_level_date"),
        )

    def get_code_count(self) -> int:
        """
        Returns the number of distinct codes this condition owns.

        Honest since the aggregates behind `codes` were given their `DISTINCT` back.
        They are built off `conditions_codes_temp`, whose grain is
        `(condition_id, code_id, valueset_id)`, so without it a code contributed by
        six sibling groupers counted six times -- which is what made this **2.58x too
        high for 17.4% of conditions**, persisted into `events.code_count` and shown
        in the activity log.

        Two codes differing only by code system are counted separately, because the
        deduplication keys on `system_id` as well. `tests/integration/
        test_condition_code_grain.py` and `tests/unit/test_sql_grain.py` both fail if
        either half of that regresses.
        """

        return len(self.codes)


@dataclass(frozen=True)
class DbConditionRsgMatch:
    """
    A condition identified by the child-RSG SNOMED codes that name it.

    Deliberately carries **no** `codes`. Its one consumer
    (`services/testing.py::_map_rc_codes_to_conditions`) reads `id`, `version` and
    `child_rsg_snomed_codes` to map an RR's reportable codes onto conditions, and
    aggregating every code of every matched condition to satisfy a field nobody
    reads cost 412ms against 15ms without it -- measured on the worst case.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
    coverage_level: str | None
    child_rsg_snomed_codes: list[str]


@dataclass(frozen=True)
class ConditionSummary:
    """
    High-level information for a condition.
    """

    id: UUID
    display_name: str
    rsg_codes: list[CodeLabel]

    @classmethod
    def from_db_row(cls, data: dict):
        """
        Creates an object from a read from the DB.
        """
        return cls(
            id=data["id"],
            display_name=data["display_name"],
            rsg_codes=[
                CodeLabel(code=c["code"], display_name=c["display_name"])
                for c in data["rsg_codes"]
            ],
        )

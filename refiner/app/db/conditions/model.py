from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class DbConditionCoding:
    """
    Model for code/display pairs from conditions table JSONB columns.

    Note: System is implicit in the column name (e.g., snomed_codes, loinc_codes).
    """

    code: str
    display: str


@dataclass
class DbConditionBasicInfo:
    """
    Simple information about a condition from the database. Excludes info about code sets.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str


@dataclass
class DbCondition(DbConditionBasicInfo):
    """
    Model to represent a complete condition row from the database (row).

    This represents the full structure of the conditions table, including
    all the JSON fields that contain aggregated codes from child RSGs.
    """

    # the child RSG codes that match 1:1 with RC SNOMED codes
    # that will come **from** the RR's coded information organizer
    child_rsg_snomed_codes: list[str]
    # jsonb columns storing code/display pairs
    # this data is extracted from flat files from the TES
    # and seeded from CG's RSG children
    snomed_codes: list[DbConditionCoding]
    loinc_codes: list[DbConditionCoding]
    icd10_codes: list[DbConditionCoding]
    rxnorm_codes: list[DbConditionCoding]

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
            child_rsg_snomed_codes=row["child_rsg_snomed_codes"],
            snomed_codes=[DbConditionCoding(**c) for c in row["snomed_codes"]],
            loinc_codes=[DbConditionCoding(**c) for c in row["loinc_codes"]],
            icd10_codes=[DbConditionCoding(**c) for c in row["icd10_codes"]],
            rxnorm_codes=[DbConditionCoding(**c) for c in row["rxnorm_codes"]],
        )

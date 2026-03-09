from dataclasses import dataclass, field
from typing import Any, TypedDict
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
class DbConditionBase:
    """
    Simple information about a condition from the database. Excludes info about code sets.
    """

    id: UUID
    display_name: str
    output_name: str
    canonical_url: str
    version: str


@dataclass
class DbCondition(DbConditionBase):
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
    # and seeded from CG's RSG and ACG children
    snomed_codes: list[DbConditionCoding]
    loinc_codes: list[DbConditionCoding]
    icd10_codes: list[DbConditionCoding]
    rxnorm_codes: list[DbConditionCoding]
    cvx_codes: list[DbConditionCoding]

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
            output_name=row["output_name"],
            canonical_url=row["canonical_url"],
            version=row["version"],
            child_rsg_snomed_codes=row["child_rsg_snomed_codes"],
            snomed_codes=[DbConditionCoding(**c) for c in row["snomed_codes"]],
            loinc_codes=[DbConditionCoding(**c) for c in row["loinc_codes"]],
            icd10_codes=[DbConditionCoding(**c) for c in row["icd10_codes"]],
            rxnorm_codes=[DbConditionCoding(**c) for c in row["rxnorm_codes"]],
            cvx_codes=[DbConditionCoding(**c) for c in row["cvx_codes"]],
        )


class ConditionMapValueDict(TypedDict):
    """
    Typed dictionary version of a ConditionMapValue.
    """

    canonical_url: str
    name: str
    tes_version: str


@dataclass(frozen=True)
class ConditionMapValue:
    """
    Condition data mapped to an RSG.
    """

    canonical_url: str
    name: str
    tes_version: str

    @classmethod
    def from_dict(cls, data: ConditionMapValueDict) -> "ConditionMapValue":
        """
        Converts a payload map value dictionary into an object.

        Args:
            data (ConditionMapValueDict): Payload map data as a dict

        Returns:
            ConditionMapValue: Payload value as an object.
        """
        return cls(
            canonical_url=data["canonical_url"],
            name=data["name"],
            tes_version=data["tes_version"],
        )


# Map an RSG to CG data
@dataclass
class ConditionMappingPayload:
    """
    Maps RSG code -> ConditionMapValue.
    """

    mappings: dict[str, ConditionMapValue] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, data: dict[str, ConditionMapValueDict]
    ) -> "ConditionMappingPayload":
        """
        Converts a payload dictionary into an object.

        Args:
            data (dict[str, ConditionMapValueDict]): The payload as a dictionary.

        Returns:
            ConditionMappingPayload: The payload object.
        """
        return cls(
            mappings={
                rsg: ConditionMapValue.from_dict(value) for rsg, value in data.items()
            }
        )

    def to_dict(self) -> dict[str, ConditionMapValueDict]:
        """
        Converts the payload object back into a dictionary.
        """

        return {
            rsg: {
                "canonical_url": value.canonical_url,
                "name": value.name,
                "tes_version": value.tes_version,
            }
            for rsg, value in self.mappings.items()
        }

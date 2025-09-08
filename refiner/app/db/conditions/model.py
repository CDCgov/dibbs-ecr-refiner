from uuid import UUID

from pydantic import BaseModel


class DbConditionCoding(BaseModel):
    """
    Model for code/display pairs from conditions table JSONB columns.

    Note: System is implicit in the column name (e.g., snomed_codes, loinc_codes).
    """

    code: str
    display: str


class DbCondition(BaseModel):
    """
    Model to represent a complete condition row from the database (row).

    This represents the full structure of the conditions table, including
    all the JSON fields that contain aggregated codes from child RSGs.
    """

    id: UUID
    display_name: str
    canonical_url: str
    version: str
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

from typing import TypedDict


class CodeableConcept(TypedDict):
    """
    Individual code with display name.

    This is our most basic building block. Used to represent any single clinical
    code (LOINC, SNOMED, etc) with its display name. `TypedDict` ensures type
    safety for dictionary-like structures.

    Fields:
        code (str): The unique identifier from the coding system (e.g., "50711007" for SNOMED)
        display (str): Human readable description of the code (e.g., "Hepatitis C Virus Infection")
    """

    code: str
    display: str


class IncludedGrouper(TypedDict):
    """
    Structure for APHL's Terminology Exchange Service's reportable condition groupers.

    Represents SNOMED CT codes that are designated as reportable conditions in APHL's
    Terminology Exchange Service. These codes act as groupers that may include other
    related conditions. In the API, they're identified by the pattern 'rs-grouper-{SnomedCode}'.

    Example JSON structure in database:

    1. For a single grouper in `filters.included_groupers` table:

        [
            {"condition": "38362002", "display": "Dengue Virus Infection"},
        ]

    2. For two or more groupers in `filters.included_geroupers` table:

        [
            {"condition": "95891005", "display": "Influenza-like Illness (ILI)"},
            {"condition": "772828001", "display": "Novel Influenza A Virus Infections"}
        ]

    Fields:
        condition (str): SNOMED CT code representing the reportable condition
        display (str): Human-readable name of the reportable condition
    """

    condition: str
    display: str


class GrouperRow(TypedDict):
    """
    Raw grouper data as stored in database.

    Represents a single row from the groupers table, where each condition (identified by
    a SNOMED CT code) maps to multiple related codes from different terminology systems
    (LOINC, SNOMED CT, ICD-10, RxNorm). Each *_codes column contains a JSON array of
    CodeableConcept-compatible structures. For example:

    Example row:
        {
            "condition": "36653000",
            "display_name": "Rubella",
            "loinc_codes": "[{"code": "104063-3", "display": "Body temperature - Groin"}, ...]",
            "snomed_codes": "[{"code": "10082001", "display": "Progressive rubella panencephalitis"}, ...]",
            "icd10_codes": "[{"code": "B06", "display": "Rubella [German measles]"}, ...]",
            "rxnorm_codes": "[]"
        }

    Fields:
        condition (str): Primary SNOMED CT code identifying the reportable condition
        display_name (str): Human-readable name of the condition
        loinc_codes (str): JSON string containing array of LOINC codes and their displays
        snomed_codes (str): JSON string containing array of related SNOMED CT codes and displays
        icd10_codes (str): JSON string containing array of ICD-10 codes and displays
        rxnorm_codes (str): JSON string containing array of RxNorm codes and displays
    """

    condition: str
    display_name: str
    loinc_codes: str
    snomed_codes: str
    icd10_codes: str
    rxnorm_codes: str


class FilterRow(TypedDict):
    """
    Raw filter data as stored in database.

    Represents a single row from the filters table, where each condition (identified by
    a SNOMED CT code) can include multiple user-defined codes from different terminology
    systems (LOINC, SNOMED CT, ICD-10, RxNorm) and references to other reportable
    conditions. Each ud_*_codes column contains a JSON array of CodeableConcept-compatible
    structures, and included_groupers contains an IncludedGrouper-compatible structure of
    itself and potentially user defined related conditions.

    Example row:
        {
            "condition": "38362002",
            "display_name": "Dengue Virus Infection",
            "ud_loinc_codes": "[]",
            "ud_snomed_codes": "[]",
            "ud_icd10_codes": "[]",
            "ud_rxnorm_codes": "[]",
            "included_groupers": "[{"condition": "38362002", "display": "Dengue Virus Infection"}]"
        }

    Fields:
        condition (str): Primary SNOMED CT code identifying the filter condition
        display_name (str): Human-readable name of the condition
        ud_loinc_codes (str): JSON string containing array of user-defined LOINC codes and displays
        ud_snomed_codes (str): JSON string containing array of user-defined SNOMED CT codes and displays
        ud_icd10_codes (str): JSON string containing array of user-defined ICD-10 codes and displays
        ud_rxnorm_codes (str): JSON string containing array of user-defined RxNorm codes and displays
        included_groupers (str): JSON string containing array of referenced reportable conditions
    """

    condition: str
    display_name: str
    ud_loinc_codes: str
    ud_snomed_codes: str
    ud_icd10_codes: str
    ud_rxnorm_codes: str
    included_groupers: str

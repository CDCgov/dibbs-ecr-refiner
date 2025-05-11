from ..core.exceptions import ZipValidationError
from .db import get_value_sets_for_condition


def get_clinical_services(condition_codes: str) -> list[dict]:
    """
    Get clinical services associated with condition codes.

    This a function that loops through the provided condition codes. For each
    condition code provided, it returns the value set of clinical services associated
    with that condition.

    Args:
        condition_codes: SNOMED condition codes to look up in the TES DB.

    Returns:
        list[dict]: List of clinical services associated with a condition code.
    """

    clinical_services_list = []
    conditions_list = condition_codes.split(",")
    for condition in conditions_list:
        clinical_services_list.append(get_value_sets_for_condition(condition))
    return clinical_services_list


def load_section_loincs(loinc_json: dict) -> tuple[list, dict]:
    """
    Read section LOINC JSON to create parsing and validation constants.

    Args:
        loinc_json: Nested dictionary containing the nested section LOINCs.

    Returns:
        tuple[list, dict]: A tuple containing:
            - list: All section LOINCs currently supported by the API
            - dict: All required section LOINCs to pass validation
    """

    # LOINC codes for eICR sections our refiner API accepts
    section_list = list(loinc_json.keys())

    # dictionary of the required eICR sections'
    # LOINC section code, root templateId and extension, displayName, and title
    # to be used to create minimal sections and trigger code templates to support validation
    section_details = {
        loinc: {
            "minimal_fields": details.get("minimal_fields"),
            "trigger_code_template": details.get("trigger_code_template"),
        }
        for loinc, details in loinc_json.items()
        if details.get("required")
    }
    return (section_list, section_details)


def create_clinical_services_dict(
    clinical_services_list: list[dict],
) -> dict[str, list[str]]:
    """
    Transform Trigger Code Reference API response to system-based dictionary.

    Converts the API response to use system names as keys and code lists as values.
    Systems are normalized to recognized shorthand names for XPath construction and
    system name variant filtering.


    Args:
        clinical_services_list: List of clinical services from TCR API

    Returns:
        dict[str, list[str]]: Transformed dictionary with shorthand system names

    Raises:
        ZipValidationError: If an unrecognized clinical service system is found
    """

    system_dict = {
        "http://hl7.org/fhir/sid/icd-9-cm": "icd9",
        "http://hl7.org/fhir/sid/icd-10-cm": "icd10",
        "http://snomed.info/sct": "snomed",
        "http://loinc.org": "loinc",
        "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm",  # TODO
        "http://hl7.org/fhir/sid/cvx": "cvx",  # TODO
    }

    transformed_dict = {}
    for clinical_services in clinical_services_list:
        for service_type, entries in clinical_services.items():
            for entry in entries:
                system = entry.get("system")
                if system not in system_dict:
                    raise ZipValidationError(
                        message=f"Unrecognized clinical service system: {system}",
                        details={
                            "system": system,
                            "valid_systems": list(system_dict.keys()),
                        },
                    )
                shorthand_system = system_dict[system]
                if shorthand_system not in transformed_dict:
                    transformed_dict[shorthand_system] = []
                transformed_dict[shorthand_system].extend(entry.get("codes", []))
    return transformed_dict

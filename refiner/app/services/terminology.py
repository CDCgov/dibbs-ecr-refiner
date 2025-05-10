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

import sqlite3

_TES_DB_URL = "./app/tes.db"


def get_value_sets_for_condition(condition_code: str) -> dict:
    """
    For a given condition, queries and returns the value set of clinical
    services associated with that condition.

    :param condition_code: A query param supplied as a string representing a
      single SNOMED condition code.
    :param filter_concepts: (Optional) A comma-separated string of
      value set types (defined by the abbreviation codes above) to
      keep. By default, all (currently) 6 value set types are
      returned; use this parameter to return only types of interest.
    :return: An HTTP Response containing the value sets of the queried code.
    """
    if condition_code is None or condition_code == "":
        return {}
    else:
        clean_snomed_code = get_clean_snomed_code(condition_code)
        concepts_list = _get_concepts_list_tes(clean_snomed_code)
        values = _get_concepts_dict(concepts_list)
    return values


def _get_concepts_dict(concept_list: list[tuple]) -> dict:
    """
    This function parses a list of tuples containing data on clinical codes
    into a dictionary for use in the /get-value-sets API endpoint.

    There is an optional parameter to return select value set type(s)
    specified as either a string or a list.

    :param concept_list: A list of tuples with value set type,
    a delimited-string of relevant codes and code systems as objects within.
    :param filter_concept_list: (Optional) List of value set types
    specified to keep. By default, all (currently) 6 value set types are
    returned; use this parameter to return only types of interest.
    :return: A nested dictionary with value set type as the key, a list
    of the relevant codes and code systems as objects within.
    """
    # Convert to the final structured format
    concept_dict = {}
    for concept_type, codes_string, system in concept_list:
        # If concept_type is not yet in the dictionary, initialize
        if concept_type not in concept_dict:
            concept_dict[concept_type] = []
        # Append a new entry with the codes and their system
        concept_dict[concept_type].append(
            {"codes": codes_string.split("|"), "system": system}
        )

    return concept_dict


def _get_concepts_list_tes(snomed_code: list) -> list[tuple]:
    """
    Given a SNOMED code, this function runs a SQL query to get the
    concept type, concept codes, and concept system
    from the TES database grouped by concept type and system. It
    also uses the GEM crosswalk tables to find any ICD-9 conversion
    codes that might be represented under the given condition's
    umbrella.

    :param snomed_code: SNOMED code to check
    :return: A list of tuples with concept type, a delimited-string of
      the relevant codes (including any found ICD-9 conversions, if they
      exist), and code systems as objects within.
    """

    query = """
    SELECT
        ct.type,
        GROUP_CONCAT(cs.code, '|') AS codes,
        cs.system AS system,
        GROUP_CONCAT(icd9_conversions, '|') AS crosswalk_conversions
    FROM
        condition c
    JOIN
        conditionconceptlink ccl on ccl.condition_id = c.id
    JOIN
        concepttype ct on ct.concept_id = ccl.concept_id
    JOIN
        concept cs on ct.concept_id = cs.id
    LEFT JOIN
        (SELECT icd10_code, GROUP_CONCAT(icd9_code, '|') AS icd9_conversions FROM icdcrosswalk GROUP BY icd10_code) ON gem_formatted_code = icd10_code
    WHERE
        c.id = ?
    GROUP BY
        ct.type, cs.system
    """
    # Connect to the SQLite database, execute sql query, then close
    try:
        with sqlite3.connect(_TES_DB_URL) as conn:
            cursor = conn.cursor()
            code = get_clean_snomed_code(snomed_code)[0]
            condition_id = _get_condition_id_from_snowmed_code_tes(code)
            cursor.execute(query, [condition_id])
            concept_list = cursor.fetchall()

            # We know it's not an actual error because we didn't get kicked to
            # except, so just return the lack of results
            if not concept_list:
                return []

        # Add any existing ICD-9 codes into the main code components
        # Tuples are immutable so we'll need to make some fresh ones
        refined_list = _format_icd9_crosswalks(concept_list)
        return refined_list
    except sqlite3.Error as e:
        return {"error": f"An SQL error occurred: {str(e)}"}


def _format_icd9_crosswalks(db_list: list[tuple]) -> list[tuple]:
    """
    Utility function to transform the returned tuple rows from the DB into a
    list of properly formatted three-part tuples. This function handles ICD-9
    formatting, since the GEM files only give us the relationship between ICD
    9 and 10 rather than system and OID information itself, so this inserts
    the missing formatting expected by the rest of the system.

    :param db_list: The list of returned tuples from the SQLite DB.
    :return: A list of tuples three elements long, formatted as the return for
      `get_concepts_list`.
    """
    formatted_list = []
    for vs_type in db_list:
        if vs_type[3] is not None and vs_type[3] != "":
            formatted_list.append((vs_type[0], vs_type[1], vs_type[2]))
            formatted_list.append(
                (vs_type[0], vs_type[3], "http://hl7.org/fhir/sid/icd-9-cm")
            )
        else:
            formatted_list.append((vs_type[0], vs_type[1], vs_type[2]))
    return formatted_list


def _get_condition_id_from_snowmed_code_tes(condition_code: str) -> str:
    """
    Given a condition code, this function retrieves the condition id
    """
    with sqlite3.connect(_TES_DB_URL) as conn:
        row = conn.execute(
            "SELECT id FROM condition WHERE code = ?", (condition_code,)
        ).fetchone()

    return row[0] if row else None


def get_clean_snomed_code(snomed_code: list | str | int | float) -> list:
    """
    This is a small helper function that takes a SNOMED code, sanitizes it,
    then checks to confirm only one SNOMED code has been provided.

    :param snomed_code: SNOMED code to check.
    :return: A one-item list of a cleaned SNOMED code.
    """
    clean_snomed_code = _convert_inputs_to_list(snomed_code)
    if len(clean_snomed_code) != 1:
        return {
            "error": f"{len(clean_snomed_code)} SNOMED codes provided. "
            + "Provide only one SNOMED code."
        }
    return clean_snomed_code


def _convert_inputs_to_list(value: list | str | int | float) -> list:
    """
    Small helper function that checks the type of the input.
    Our code wants items to be in a list and will transform int/float to list
    and will check if a string could potentially be a list.
    It will also remove any excess characters from the list.

    :param value: string, int, float, list to check
    :return: A list free of excess whitespace
    """
    if isinstance(value, int | float):
        return [str(value)]
    elif isinstance(value, str):
        common_delimiters = [",", "|", ";"]
        for delimiter in common_delimiters:
            if delimiter in value:
                return [val.strip() for val in value.split(delimiter) if val.strip()]
        return [value.strip()]  # No delimiter found, return the single value
    elif isinstance(value, list):
        return [str(val).strip() for val in value if str(val).strip()]
    else:
        raise ValueError("Unsupported input type for sanitation.")

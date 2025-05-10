import sqlite3

_TES_DB_URL = "./app/tes.db"


def get_value_sets_for_condition(condition_code: str) -> dict:
    """
    Query and return clinical services value set for a condition.

    Args:
        condition_code: Single SNOMED condition code as string.

    Returns:
        dict: Value sets associated with the queried code, containing:
            - Value set type as key
            - List of clinical services with their codes and systems
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
    Parse clinical code tuples into a dictionary for the get-value-sets API.

    Takes a list of tuples containing clinical code data and organizes them
    into a structured dictionary for API response.

    Args:
        concept_list: List of tuples containing:
            - Value set type
            - Delimited string of codes
            - Code systems

    Returns:
        dict: Nested dictionary with:
            - Value set type as key
            - List of relevant codes and systems as values
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
    Query TES database for concept details using SNOMED code.

    Executes SQL query to retrieve concept type, codes, and systems.
    Includes ICD-9 conversion codes found through GEM crosswalk tables.

    Args:
        snomed_code: List containing a single SNOMED code to query.

    Returns:
        list[tuple]: Each tuple contains:
            - Concept type
            - Delimited string of relevant codes (including ICD-9 conversions)
            - Code systems
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
    Format database rows for ICD-9 crosswalk entries.

    Transforms database tuple rows into properly formatted three-part tuples,
    handling ICD-9 specific formatting requirements from GEM files.

    Args:
        db_list: Raw tuple rows from SQLite database.

    Returns:
        list[tuple]: Formatted tuples containing:
            - System information
            - Code value
            - OID reference
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
    Given a condition code, this function retrieves the condition id.
    """

    with sqlite3.connect(_TES_DB_URL) as conn:
        row = conn.execute(
            "SELECT id FROM condition WHERE code = ?", (condition_code,)
        ).fetchone()

    return row[0] if row else None


def get_clean_snomed_code(snomed_code: list | str | int | float) -> list:
    """
    Sanitize and validate SNOMED code input.

    Cleans the provided SNOMED code and ensures only one code is present.

    Args:
        snomed_code: SNOMED code in various possible formats:
            - list: List containing code
            - str: String representation of code
            - int: Integer representation of code
            - float: Float representation of code

    Returns:
        list: Single-item list containing the cleaned SNOMED code.
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
    Convert various input types to a clean list.

    Handles different input types and converts them to a standardized list format,
    removing excess whitespace and characters.

    Args:
        value: Input to convert, can be:
            - list: Already in list format
            - str: String to convert
            - int: Integer to convert
            - float: Float to convert

    Returns:
        list: Cleaned list with standardized format and no excess whitespace.
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

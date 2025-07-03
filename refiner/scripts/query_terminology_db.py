import json
import os
from typing import Any

import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# constants for querying - edit these values as needed

# SNOMED code to query the groupers table
CONDITION_CODE = "840539006"

# set CODE_TO_SEARCH to None if you just want to view all codes without checking
# CODE_TO_SEARCH = None
CODE_TO_SEARCH: dict[str, str] | None = {
    # options: loinc_codes, snomed_codes, icd10_codes, rxnorm_codes
    "column": "loinc_codes",
    # the actual code to search for
    "code": "34487-9",
}


def connect_to_db() -> tuple[psycopg.Connection, psycopg.Cursor]:
    """
    Connect to the terminology database.

    Returns:
        Tuple of database connection and cursor
    """
    db_url = os.getenv("DB_URL")
    conn = psycopg.connect(db_url)
    cursor = conn.cursor()
    return conn, cursor


def fetch_grouper_by_condition(
    cursor: psycopg.Cursor, condition_code: str
) -> dict[str, Any] | None:
    """
    Fetch a grouper record by its condition code.

    Args:
        cursor: Database cursor for executing queries
        condition_code: The condition code to search for

    Returns:
        Dictionary with the grouper data or None if not found
    """

    cursor.execute(
        """
        SELECT condition, display_name, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes
        FROM groupers
        WHERE condition = %s
        """,
        (condition_code,),
    )

    row = cursor.fetchone()
    if not row:
        return None

    return {
        "condition": row[0],
        "display_name": row[1],
        "loinc_codes": json.loads(row[2]) if row[2] else [],
        "snomed_codes": json.loads(row[3]) if row[3] else [],
        "icd10_codes": json.loads(row[4]) if row[4] else [],
        "rxnorm_codes": json.loads(row[5]) if row[5] else [],
    }


def check_for_code_in_column(
    grouper_data: dict[str, Any], code_info: dict[str, str]
) -> bool:
    """
    Check if a specific code exists in the specified column of the grouper.

    Args:
        grouper_data: Dictionary with grouper data
        code_info: Dictionary with column and code to search for

    Returns:
        True if code is found, False otherwise
    """

    column = code_info["column"]
    code_to_find = code_info["code"]

    if column not in grouper_data:
        return False

    codes = grouper_data[column]

    # check in the code array
    for code_obj in codes:
        # handle different possible structures
        if (
            isinstance(code_obj, dict)
            and "code" in code_obj
            and code_obj["code"] == code_to_find
        ):
            return True
        elif isinstance(code_obj, str) and code_obj == code_to_find:
            return True

    return False


def create_code_details_table(code_type: str, codes: list[dict[str, Any]]) -> Table:
    """
    Create a Rich table to display code details.

    Args:
        code_type: Type of the codes (LOINC, SNOMED, etc.)
        codes: List of code objects

    Returns:
        Rich Table object
    """
    table = Table(title=f"{code_type} Codes")

    # determine columns based on first code object
    if not codes:
        table.add_column("No codes found", style="red")
        return table

    # add columns based on the keys in the first code object
    first_code = codes[0]
    if isinstance(first_code, dict):
        for key in first_code.keys():
            table.add_column(key.capitalize(), style="cyan")

        # add rows for each code
        for code_obj in codes:
            table.add_row(*[str(code_obj.get(key, "")) for key in first_code.keys()])
    else:
        # simple string codes
        table.add_column("Code", style="cyan")
        for code in codes:
            table.add_row(str(code))

    return table


def display_grouper_details(grouper_data: dict[str, Any], console: Console) -> None:
    """
    Display detailed information about a grouper.

    Args:
        grouper_data: Dictionary with grouper data
        console: Rich console for output formatting
    """

    console.print(
        f"\n[bold green]Grouper Details for Condition: [cyan]{grouper_data['condition']}[/cyan][/bold green]"
    )
    console.print(f"Display Name: [yellow]{grouper_data['display_name']}[/yellow]")

    # show code counts
    counts_table = Table(title="Code Counts")
    counts_table.add_column("Code Type", style="blue")
    counts_table.add_column("Count", style="magenta", justify="right")

    for code_type in ["loinc_codes", "snomed_codes", "icd10_codes", "rxnorm_codes"]:
        display_name = code_type.replace("_codes", "").upper()
        count = len(grouper_data[code_type])
        counts_table.add_row(display_name, str(count))

    console.print(counts_table)

    # display each code type in detail
    for code_type, codes in [
        ("LOINC", grouper_data["loinc_codes"]),
        ("SNOMED", grouper_data["snomed_codes"]),
        ("ICD-10", grouper_data["icd10_codes"]),
        ("RxNorm", grouper_data["rxnorm_codes"]),
    ]:
        if codes:
            console.print(f"\n[bold blue]{code_type} Codes ({len(codes)})[/bold blue]")
            console.print(create_code_details_table(code_type, codes))


def search_for_specific_code(
    grouper_data: dict[str, Any], code_info: dict[str, str], console: Console
) -> None:
    """
    Search for a specific code in the grouper data and display the result.

    Args:
        grouper_data: Dictionary with grouper data
        code_info: Dictionary with column and code to search for
        console: Rich console for output formatting
    """

    column = code_info["column"]
    code = code_info["code"]

    # get readable column name
    column_display = column.replace("_codes", "").upper()

    found = check_for_code_in_column(grouper_data, code_info)

    if found:
        console.print(
            f"\n[bold green]✓ Code [cyan]{code}[/cyan] FOUND in {column_display} codes[/bold green]"
        )

        # find and display the specific code details
        codes = grouper_data[column]
        matching_codes = []

        for code_obj in codes:
            if (
                isinstance(code_obj, dict)
                and "code" in code_obj
                and code_obj["code"] == code
            ):
                matching_codes.append(code_obj)
            elif isinstance(code_obj, str) and code_obj == code:
                matching_codes.append(code_obj)

        if matching_codes:
            console.print("\n[bold blue]Matching Code Details:[/bold blue]")
            console.print(json.dumps(matching_codes, indent=2))
    else:
        console.print(
            f"\n[bold red]✗ Code [cyan]{code}[/cyan] NOT FOUND in {column_display} codes[/bold red]"
        )


def main() -> None:
    """
    Main function to run the script.
    """

    console = Console()
    console.print("[bold blue]Terminology Database Query Tool[/bold blue]")

    try:
        conn, cursor = connect_to_db()

        # fetch grouper by condition code
        grouper_data = fetch_grouper_by_condition(cursor, CONDITION_CODE)

        if not grouper_data:
            console.print(
                f"[bold red]No grouper found with condition code: {CONDITION_CODE}[/bold red]"
            )
            return

        # display grouper details
        display_grouper_details(grouper_data, console)

        # check for specific code if requested
        if CODE_TO_SEARCH:
            search_for_specific_code(grouper_data, CODE_TO_SEARCH, console)

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    load_dotenv()
    main()

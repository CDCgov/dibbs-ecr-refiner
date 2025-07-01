import json
import os
from typing import Any

import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# expected schema structure for validation
EXPECTED_TABLES = {
    "groupers": {
        "condition": "TEXT PRIMARY KEY",
        "display_name": "TEXT",
        "loinc_codes": "TEXT",
        "snomed_codes": "TEXT",
        "icd10_codes": "TEXT",
        "rxnorm_codes": "TEXT",
    },
    "filters": {
        "condition": "TEXT PRIMARY KEY",
        "display_name": "TEXT",
        "ud_loinc_codes": "TEXT",
        "ud_snomed_codes": "TEXT",
        "ud_icd10_codes": "TEXT",
        "ud_rxnorm_codes": "TEXT",
        "included_groupers": "TEXT",
    },
}


def validate_schema(cursor: psycopg.Cursor, console: Console) -> list[str]:
    """
    Validate database schema against expected structure.

    Args:
        cursor: Database cursor for executing schema queries
        console: Rich console for output formatting

    Returns:
        List of error messages, empty if schema is valid
    """

    console.print("\n[bold blue]Validating Database Schema...[/bold blue]")

    errors: list[str] = []

    # get all tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = {row[0] for row in cursor.fetchall()}

    # create validation table
    validation_table = Table(title="Schema Validation")
    validation_table.add_column("Table", style="cyan")
    validation_table.add_column("Status", style="green")
    validation_table.add_column("Details", style="yellow")

    # check each table
    for table in EXPECTED_TABLES:
        if table not in tables:
            errors.append(f"Missing table: {table}")
            validation_table.add_row(
                table, "[red]FAILED[/red]", "Table not found in database"
            )
            continue

        # 1. Get column names and data types
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
        """,
            (table,),
        )
        columns = {row[0]: row[1] for row in cursor.fetchall()}

        # 2. Get primary key columns
        cursor.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
        """,
            (table,),
        )
        primary_keys = {row[0] for row in cursor.fetchall()}

        table_errors = []
        for col, expected_type in EXPECTED_TABLES[table].items():
            expected_type = expected_type.lower().replace(" primary key", "")
            actual_type = columns.get(col, "").lower()

            if col not in columns:
                table_errors.append(f"Missing column: {col}")
                continue

            if col in primary_keys:
                if "primary key" not in EXPECTED_TABLES[table][col].lower():
                    table_errors.append(f"Unexpected primary key: {col}")
            else:
                if "primary key" in EXPECTED_TABLES[table][col].lower():
                    table_errors.append(f"Column {col} should be PRIMARY KEY")

            if actual_type != expected_type:
                table_errors.append(
                    f"Type mismatch for {col}: expected {expected_type}, got {actual_type}"
                )

        if table_errors:
            errors.extend(f"{table}: {err}" for err in table_errors)
            validation_table.add_row(
                table, "[red]FAILED[/red]", "\n".join(table_errors)
            )
        else:
            validation_table.add_row(
                table, "[green]OK[/green]", f"{len(columns)} columns validated"
            )

    console.print(validation_table)

    if not errors:
        console.print("[green]✓ Schema validation passed[/green]")

    return errors


def get_row_counts(cursor: psycopg.Cursor) -> dict[str, dict[str, Any]]:
    """
    Get row counts and sample entries for each table.

    Args:
        cursor: Database cursor for executing count queries

    Returns:
        Dictionary containing statistics for each table
    """

    table_stats: dict[str, dict[str, Any]] = {}

    for table in EXPECTED_TABLES:
        # get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        # get a sample entry if table is not empty
        sample = None
        if count > 0:
            if table == "groupers":
                cursor.execute(
                    """
                    SELECT condition, display_name
                    FROM groupers
                    LIMIT 1
                    """
                )
                result = cursor.fetchone()
                sample = (result[0], result[1])
            elif table == "filters":
                cursor.execute(
                    """
                    SELECT condition, display_name
                    FROM filters
                    LIMIT 1
                    """
                )
                result = cursor.fetchone()
                sample = (result[0], result[1])

        table_stats[table] = {"count": count, "sample": sample}

    return table_stats


def create_row_counts_table(stats: dict[str, dict[str, Any]]) -> Table:
    """
    Create a Rich table to display row counts.

    Args:
        stats: Dictionary of table statistics

    Returns:
        Rich Table object
    """

    counts_table = Table(title="Database Statistics")
    counts_table.add_column("Table", style="cyan")
    counts_table.add_column("Row Count", style="green", justify="right")
    counts_table.add_column("Sample Entry", style="yellow")

    for table, data in stats.items():
        count = data["count"]
        sample = data["sample"]

        # format count with commas
        formatted_count = f"{count:,}"

        # format sample entry
        sample_text = "No entries" if sample is None else f"'{sample[1]}' ({sample[0]})"

        # add row with appropriate color based on count
        if count == 0:
            counts_table.add_row(
                table,
                f"[red]{formatted_count}[/red]",
                "[italic red]Empty table[/italic red]",
            )
        else:
            counts_table.add_row(table, formatted_count, sample_text)

    return counts_table


def get_grouper_stats(cursor: psycopg.Cursor) -> dict[str, int]:
    """
    Get statistics about groupers and their codes.

    Args:
        cursor: Database cursor for executing queries

    Returns:
        Dictionary of statistics with counts

    SQL Queries Used:
        - SELECT COUNT(*) FROM groupers
        - SELECT COUNT(*) FROM groupers WHERE {code_type} != '[]'
        - SELECT COUNT(*) FROM groupers WHERE all code arrays are empty
        - SELECT COUNT(*) FROM groupers WHERE display_name IS NOT NULL
    """

    stats: dict[str, int] = {}

    # total groupers
    cursor.execute("SELECT COUNT(*) FROM groupers")
    stats["total_groupers"] = cursor.fetchone()[0]

    # groupers with each code type
    for code_type in ["loinc_codes", "snomed_codes", "icd10_codes", "rxnorm_codes"]:
        cursor.execute(f"SELECT COUNT(*) FROM groupers WHERE {code_type} != '[]'")
        stats[f"with_{code_type}"] = cursor.fetchone()[0]

    # groupers with no codes
    cursor.execute("""
        SELECT COUNT(*) FROM groupers
        WHERE loinc_codes = '[]'
          AND snomed_codes = '[]'
          AND icd10_codes = '[]'
          AND rxnorm_codes = '[]'
    """)
    stats["no_codes"] = cursor.fetchone()[0]

    # display name stats
    cursor.execute(
        "SELECT COUNT(*) FROM groupers WHERE display_name IS NOT NULL AND display_name != ''"
    )
    stats["with_display_name"] = cursor.fetchone()[0]
    stats["without_display_name"] = stats["total_groupers"] - stats["with_display_name"]

    return stats


def get_sample_rows(
    cursor: psycopg.Cursor,
    table: str,
    columns: str,
    limit: int = 5,
    random: bool = False,
) -> list[tuple]:
    """
    Get sample rows from specified table.

    Args:
        cursor: Database cursor for executing queries
        table: Table name to query
        columns: Columns to select
        limit: Maximum number of rows to return
        random: Whether to randomize selection

    Returns:
        List of row tuples

    SQL Query Used:
        SELECT {columns} FROM {table} [ORDER BY RANDOM()] LIMIT {limit}
    """

    order_by = "ORDER BY RANDOM()" if random else ""
    cursor.execute(f"SELECT {columns} FROM {table} {order_by} LIMIT {limit}")
    return cursor.fetchall()


def limit_codes(column: str) -> list[dict[str, str]] | str:
    """
    Limit the number of codes displayed in output.

    Args:
        column: JSON string containing array of code objects

    Returns:
        List of first 20 code objects if valid JSON array,
        otherwise original string
    """

    try:
        codes = json.loads(column)
        if isinstance(codes, list):
            return codes[:20]
        return column
    except (json.JSONDecodeError, TypeError):
        return column


def create_stats_table(stats: dict[str, int]) -> Table:
    """
    Create formatted table for statistics display.

    Args:
        stats: Dictionary of statistic names and values

    Returns:
        Formatted rich Table object
    """

    table = Table(title="Grouper Statistics")
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Count", style="magenta", justify="right")

    # add rows in specific order
    for metric in [
        ("total_groupers", "Total Groupers"),
        ("with_loinc_codes", "Groupers with LOINC Codes"),
        ("with_snomed_codes", "Groupers with SNOMED Codes"),
        ("with_icd10_codes", "Groupers with ICD-10 Codes"),
        ("with_rxnorm_codes", "Groupers with RxNorm Codes"),
        ("no_codes", "Groupers with No Codes"),
        ("with_display_name", "Groupers with Display Name"),
        ("without_display_name", "Groupers without Display Name"),
    ]:
        table.add_row(metric[1], str(stats[metric[0]]))

    return table


def run_checks() -> None:
    """
    Run all database validation checks and display results.
    """

    console = Console()
    console.print("\n[bold blue]Running Grouper Table Checks...[/bold blue]")

    # setup database connection
    with psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    ) as conn:
        with conn.cursor() as cursor:
            # validate schema
            errors = validate_schema(cursor, console)
            if errors:
                console.print(
                    "\n[bold red]Schema validation failed. Aborting checks.[/bold red]"
                )
                return

            # get and display row counts
            row_counts = get_row_counts(cursor)
            console.print("\n[bold blue]Table Row Counts[/bold blue]")
            console.print(create_row_counts_table(row_counts))

            # get and display statistics
            stats = get_grouper_stats(cursor)
            console.print("\n[bold blue]Grouper Statistics[/bold blue]")
            console.print(create_stats_table(stats))

            # display sample groupers with code counts
            console.print("\n[bold blue]Sample Groupers[/bold blue]")
            sample_rows = get_sample_rows(
                cursor,
                "groupers",
                """
                condition,
                display_name,
                json_array_length(NULLIF(loinc_codes, '')::json),
                json_array_length(NULLIF(snomed_codes, '')::json),
                json_array_length(NULLIF(icd10_codes, '')::json),
                json_array_length(NULLIF(rxnorm_codes, '')::json)
                """,
                limit=5,
            )

            sample_table = Table(title="Sample Groupers")
            sample_table.add_column("Condition Code", style="cyan", justify="left")
            sample_table.add_column("Display Name", style="green", justify="left")
            sample_table.add_column("LOINC Count", style="magenta", justify="right")
            sample_table.add_column("SNOMED Count", style="magenta", justify="right")
            sample_table.add_column("ICD-10 Count", style="magenta", justify="right")
            sample_table.add_column("RxNorm Count", style="magenta", justify="right")

            for row in sample_rows:
                sample_table.add_row(
                    *[str(col) if col is not None else "" for col in row]
                )
            console.print(sample_table)

            # display detailed view of random grouper
            console.print("\n[bold blue]Sample Groupers[/bold blue]")
            detail_rows = get_sample_rows(
                cursor,
                "groupers",
                "condition, display_name, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes",
                limit=1,
                random=True,
            )

            detail_table = Table(title="Sample Groupers")
            detail_table.add_column("Condition", style="cyan", justify="left")
            detail_table.add_column("Display Name", style="green", justify="left")
            detail_table.add_column("LOINC Codes", style="magenta", justify="left")
            detail_table.add_column("SNOMED Codes", style="magenta", justify="left")
            detail_table.add_column("ICD-10 Codes", style="magenta", justify="left")
            detail_table.add_column("RxNorm Codes", style="magenta", justify="left")

            for row in detail_rows:
                detail_table.add_row(
                    str(row[0]),
                    str(row[1]),
                    json.dumps(limit_codes(row[2])),
                    json.dumps(limit_codes(row[3])),
                    json.dumps(limit_codes(row[4])),
                    json.dumps(limit_codes(row[5])),
                )
            console.print(detail_table)

            # display sample filters
            console.print("\n[bold blue]Sample Filters[/bold blue]")
            filter_rows = get_sample_rows(
                cursor,
                "filters",
                "condition, display_name, included_groupers",
                limit=5,
                random=True,
            )

            filters_table = Table(title="Sample Filters")
            filters_table.add_column("Condition", style="cyan", justify="left")
            filters_table.add_column("Display Name", style="green", justify="left")
            filters_table.add_column(
                "Included Groupers", style="magenta", justify="left"
            )

            for row in filter_rows:
                filters_table.add_row(
                    *[str(col) if col is not None else "" for col in row]
                )
            console.print(filters_table)


if __name__ == "__main__":
    load_dotenv()
    run_checks()

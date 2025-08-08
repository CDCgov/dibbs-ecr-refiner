import os
import pathlib
import sys
from collections.abc import Callable
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection, Cursor
from psycopg.rows import dict_row
from rich.console import Console
from rich.table import Table

# this list defines the critical sanity checks
DB_CHECKS: list[dict[str, Any]] = [
    {
        "title": "Conditions Table Populated",
        "query": "SELECT COUNT(*) AS count FROM conditions;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "The 'conditions' table is empty. The seeding script may have failed.",
    },
    {
        "title": "Configurations Table Populated",
        "query": "SELECT COUNT(*) AS count FROM configurations;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "The 'configurations' table is empty. Seeding test data may have failed.",
    },
    {
        "title": "No Conditions with Empty Child SNOMED Arrays",
        "query": "SELECT COUNT(*) AS count FROM conditions WHERE array_length(child_rsg_snomed_codes, 1) IS NULL;",
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found conditions with no child SNOMED codes, indicating an aggregation error.",
    },
    {
        "title": "Child SNOMED Codes are Unique to a Single Condition",
        "query": """
            SELECT COUNT(*) as count
            FROM (
                SELECT
                    code,
                    COUNT(DISTINCT canonical_url) as url_count
                FROM (
                    SELECT
                        unnest(child_rsg_snomed_codes) AS code,
                        canonical_url
                    FROM conditions
                ) as unnested_with_url
                GROUP BY code
                HAVING COUNT(DISTINCT canonical_url) > 1
            ) as duplicates;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found a child SNOMED code associated with multiple different conditions (canonical_urls).",
    },
    {
        "title": "Configuration Family/Version Integrity",
        "query": """
            SELECT COUNT(*) as count FROM (
                SELECT family_id, version
                FROM configurations
                GROUP BY family_id, version
                HAVING COUNT(*) > 1
            ) duplicates;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found duplicate family_id/version combinations, violating UNIQUE constraint.",
    },
    {
        "title": "All Activations Reference Valid Configurations",
        "query": """
            SELECT COUNT(*) as count
            FROM activations a
            LEFT JOIN configurations c ON a.configuration_id = c.id
            WHERE c.id IS NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found activations referencing non-existent configurations.",
    },
    {
        "title": "Configuration JSON Fields are Valid",
        "query": """
            SELECT COUNT(*) as count
            FROM configurations
            WHERE NOT (
                jsonb_typeof(included_conditions) = 'array' AND
                jsonb_typeof(loinc_codes_additions) = 'array' AND
                jsonb_typeof(snomed_codes_additions) = 'array' AND
                jsonb_typeof(icd10_codes_additions) = 'array' AND
                jsonb_typeof(rxnorm_codes_additions) = 'array' AND
                jsonb_typeof(custom_codes) = 'array'
            );
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found configurations with malformed JSON fields.",
    },
    {
        "title": "No Multiple Active Configurations Per Condition",
        "query": """
            SELECT COUNT(*) as count FROM (
                SELECT jurisdiction_id, snomed_code
                FROM activations
                WHERE deactivated_at IS NULL
                GROUP BY jurisdiction_id, snomed_code
                HAVING COUNT(*) > 1
            ) duplicates;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found multiple active configurations for same jurisdiction/SNOMED combination.",
    },
]

# this list defines warning checks (non-critical issues)
WARNING_CHECKS: list[dict[str, Any]] = [
    {
        "title": "Configurations Without Labels",
        "query": """
            SELECT COUNT(*) as count
            FROM configurations c
            LEFT JOIN configuration_labels cl ON c.id = cl.configuration_id
            WHERE cl.configuration_id IS NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found configurations without any labels (may be intentional).",
    },
    {
        "title": "Configurations Without Activations",
        "query": """
            SELECT COUNT(*) as count
            FROM configurations c
            LEFT JOIN activations a ON c.id = a.configuration_id
            WHERE a.configuration_id IS NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found configurations that are not activated in any jurisdiction.",
    },
    {
        "title": "Labels Not Assigned to Any Configuration",
        "query": """
            SELECT COUNT(*) as count
            FROM labels l
            LEFT JOIN configuration_labels cl ON l.id = cl.label_id
            WHERE cl.label_id IS NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "Found labels that are not assigned to any configuration.",
    },
]


def get_db_connection(console: Console) -> Connection:
    """
    Constructs a DB connection string from environment variables and connects.
    """

    try:
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        dbname = os.getenv("POSTGRES_DB")
        port = os.getenv("POSTGRES_PORT")
        host = "localhost"  # Correct for connecting from host to container

        if not all([user, password, dbname, port]):
            raise ValueError(
                "😓 Missing required environment variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT"
            )

        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        return psycopg.connect(db_url, row_factory=dict_row, autocommit=True)

    except (psycopg.OperationalError, ValueError) as error:
        console.print(
            "[bold red]💥 FATAL: Could not connect to the database.[/bold red]\n"
            "Please ensure the Docker container is running and all required environment variables are set correctly in the .env file.\n"
            f"💬 Error: {error}",
        )
        sys.exit(1)


def run_check(
    cursor: Cursor,
    console: Console,
    title: str,
    query: str,
    failure_condition: Callable[[list[dict[str, Any]]], bool],
    failure_message: str,
    check_type: str = "CRITICAL",
) -> bool:
    """
    Runs a single database check and prints the result.
    """

    check_emoji = "🔎" if check_type == "CRITICAL" else "⚠️"
    console.print(
        f"{check_emoji} Running {check_type.lower()} check: [bold cyan]{title}[/bold cyan]...",
        end="",
    )

    cursor.execute(query)
    result = cursor.fetchall()
    if failure_condition(result):
        failed_emoji = "❌" if check_type == "CRITICAL" else "⚠️"
        console.print(
            f" [bold red]{failed_emoji} {'FAILED' if check_type == 'CRITICAL' else 'WARNING'}[/bold red]"
        )
        console.print(f"    💬 Reason: {failure_message}")
        if result and result[0] and result[0].get("count", 0) > 0:
            console.print(f"    📊 Count: {result[0]['count']}")
        return False
    else:
        console.print(" [bold green]✅ PASSED[/bold green]")
        return True


def display_summary_stats(cursor: Cursor, console: Console) -> None:
    """
    Displays a summary of row counts for the new schema's key tables.
    """

    console.rule()
    console.print("\n[bold blue]📊 Database Summary Statistics[/bold blue]\n")
    stats_table = Table(title="Table Row Counts")
    stats_table.add_column("Table Name", style="cyan")
    stats_table.add_column("Row Count", style="magenta", justify="right")

    tables_to_check = [
        "jurisdictions",
        "users",
        "labels",
        "conditions",
        "configurations",
        "configuration_labels",
        "activations",
    ]

    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table};")
        row = cursor.fetchone()
        count = row["count"] if row is not None else 0
        stats_table.add_row(table, f"{count:,}")

    console.print(stats_table)


def display_family_stats(cursor: Cursor, console: Console) -> None:
    """
    Displays configuration family statistics.
    """

    console.print("\n[bold blue]👨‍👩‍👧‍👦 Configuration Family Statistics[/bold blue]\n")

    cursor.execute("""
        SELECT
            family_id,
            COUNT(*) as version_count,
            MAX(version) as latest_version,
            string_agg(DISTINCT name, ', ') as names
        FROM configurations
        GROUP BY family_id
        ORDER BY family_id;
    """)

    family_table = Table(title="Configuration Families")
    family_table.add_column("Family ID", style="cyan", justify="right")
    family_table.add_column("Versions", style="magenta", justify="right")
    family_table.add_column("Latest", style="green", justify="right")
    family_table.add_column("Name", style="yellow")

    families = cursor.fetchall()
    if families:
        for row in families:
            name_display = row["names"]
            if len(name_display) > 50:
                name_display = name_display[:47] + "..."

            family_table.add_row(
                str(row["family_id"]),
                str(row["version_count"]),
                str(row["latest_version"]),
                name_display,
            )

        console.print(family_table)
    else:
        console.print("[yellow]No configuration families found.[/yellow]")


def display_activation_stats(cursor: Cursor, console: Console) -> None:
    """
    Displays activation statistics by jurisdiction.
    """

    console.print("\n[bold blue]🎯 Activation Statistics[/bold blue]\n")

    cursor.execute("""
        SELECT
            j.name as jurisdiction_name,
            COUNT(CASE WHEN a.deactivated_at IS NULL THEN 1 END) as active_count,
            COUNT(CASE WHEN a.deactivated_at IS NOT NULL THEN 1 END) as inactive_count,
            COUNT(*) as total_activations
        FROM jurisdictions j
        LEFT JOIN activations a ON j.id = a.jurisdiction_id
        GROUP BY j.id, j.name
        ORDER BY j.name;
    """)

    activation_table = Table(title="Activations by Jurisdiction")
    activation_table.add_column("Jurisdiction", style="cyan")
    activation_table.add_column("Active", style="green", justify="right")
    activation_table.add_column("Inactive", style="red", justify="right")
    activation_table.add_column("Total", style="blue", justify="right")

    activations = cursor.fetchall()
    if activations:
        for row in activations:
            activation_table.add_row(
                row["jurisdiction_name"],
                str(row["active_count"]),
                str(row["inactive_count"]),
                str(row["total_activations"]),
            )

        console.print(activation_table)
    else:
        console.print("[yellow]No activation data found.[/yellow]")


def main() -> None:
    """
    Main function to orchestrate all database sanity checks.
    """

    script_dir = pathlib.Path(__file__).resolve().parent
    dotenv_path = script_dir.parent / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    console = Console()
    console.print("\n[bold blue]🧪 Running Database Sanity Checks...[/bold blue]")
    connection: Connection | None = None
    all_critical_checks_passed = True
    warnings_found = False

    try:
        connection = get_db_connection(console)
        with connection.cursor() as cursor:
            # run critical checks
            console.print("\n[bold red]🚨 Critical Checks[/bold red]")
            for check in DB_CHECKS:
                passed = run_check(
                    cursor,
                    console,
                    title=check["title"],
                    query=check["query"],
                    failure_condition=check["failure_condition"],
                    failure_message=check["failure_message"],
                    check_type="CRITICAL",
                )
                if not passed:
                    all_critical_checks_passed = False

            # run warning checks
            console.print("\n[bold yellow]⚠️ Warning Checks[/bold yellow]")
            for check in WARNING_CHECKS:
                passed = run_check(
                    cursor,
                    console,
                    title=check["title"],
                    query=check["query"],
                    failure_condition=check["failure_condition"],
                    failure_message=check["failure_message"],
                    check_type="WARNING",
                )
                if not passed:
                    warnings_found = True

            # display results
            console.rule()
            if all_critical_checks_passed:
                console.print(
                    "\n[bold green]🎉 All critical sanity checks passed![/bold green]"
                )
                if warnings_found:
                    console.print(
                        "[bold yellow]⚠️ Some warnings were found (non-critical).[/bold yellow]"
                    )

                # display comprehensive statistics
                display_summary_stats(cursor, console)
                display_family_stats(cursor, console)
                display_activation_stats(cursor, console)

                console.print(
                    "\n[bold green]✨ Database validation complete![/bold green]\n"
                )
            else:
                console.print(
                    "\n[bold red]❌ One or more critical sanity checks failed.[/bold red]"
                )
                console.print(
                    "[bold red]Database integrity issues detected. Please review and fix before proceeding.[/bold red]"
                )
                sys.exit(1)

    except psycopg.Error as error:
        console.print(
            f"\n[bold red]💥 An unexpected database error occurred: {error}[/bold red]"
        )
        sys.exit(1)
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    main()

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection, Cursor
from psycopg.rows import dict_row
from rich.console import Console
from rich.table import Table

SCRIPTS_DIR = Path(__file__).parent.parent
ENV_PATH = SCRIPTS_DIR / ".env"
TES_CG_VERSIONS = ["1.0.0", "2.0.0", "3.0.0"]

TABLES_TO_CHECK = [
    "conditions",
    "configurations",
    "jurisdictions",
    "schema_migrations",
    "sessions",
    "users",
]

# this list defines the critical sanity checks
DB_CHECKS: list[dict[str, Any]] = [
    {
        "title": "Conditions Table Populated",
        "query": "SELECT COUNT(*) AS count FROM conditions;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "The 'conditions' table is empty. The seeding script may have failed.",
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
        "title": "Expected Condition Grouper Versions Present",
        "query": "SELECT version FROM conditions GROUP BY version;",
        "failure_condition": lambda res: not all(
            v in [r["version"] for r in res] for v in TES_CG_VERSIONS
        ),
        "failure_message": "One or more expected condition grouper versions are missing.",
    },
]

# this list defines warning checks (non-critical issues)
WARNING_CHECKS: list[dict[str, Any]] = [
    # TODO:
    # warning tests that check:
    # * do we have any configurations?
    # * do we have users?
    # * do we have jurisdictions?
    # will be added in a separate PR for local versions of the db where we will need both:
    # * a covid configuration for the refiner user's jurisdiction_id
    # * an influenza configuration for the refiner user's jurisdiction_id
    # * and a user that is performing these actions in the ui associated with the above jurisdiction_id
    # _for now this should fail given the seeding logic but only as a warning_
    {
        "title": "Configurations Table Populated",
        "query": "SELECT COUNT(*) AS count FROM configurations;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "The 'configurations' table is empty. The seeding script may have failed.",
    },
    {
        "title": "All Configurations Reference Valid Conditions",
        "query": """
            SELECT COUNT(*) AS count
            FROM configurations c
            LEFT JOIN conditions cond ON c.condition_id = cond.id
            WHERE cond.id IS NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "There are configurations with invalid condition_id (not found in conditions table).",
    },
    {
        "title": "No Users Present",
        "query": "SELECT COUNT(*) AS count FROM users;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "No users found in the database.",
    },
    {
        "title": "No Jurisdictions Present",
        "query": "SELECT COUNT(*) AS count FROM jurisdictions;",
        "failure_condition": lambda res: res[0]["count"] == 0,
        "failure_message": "No jurisdictions found in the database.",
    },
    {
        "title": "All Users Reference Valid Jurisdictions",
        "query": """
            SELECT COUNT(*) AS count
            FROM users u
            LEFT JOIN jurisdictions j ON u.jurisdiction_id = j.id
            WHERE j.id IS NULL AND u.jurisdiction_id IS NOT NULL;
        """,
        "failure_condition": lambda res: res[0]["count"] > 0,
        "failure_message": "There are users with invalid jurisdiction_id (not found in jurisdictions table).",
    },
]


def get_db_connection(console: Console) -> Connection:
    """
    Constructs a DB connection string from environment variables and connects.
    """

    try:
        db_url = os.getenv("DB_URL")
        if not db_url:
            raise ValueError("😓 Missing required environment variable: DB_URL")
        return psycopg.connect(db_url, row_factory=dict_row, autocommit=True)
    except (psycopg.OperationalError, ValueError) as error:
        console.print(
            "[bold red]💥 FATAL: Could not connect to the database.[/bold red]\n"
            "Please ensure the Docker container is running and the DB_URL is set correctly in the .env file.\n"
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

    for table in TABLES_TO_CHECK:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table};")
        row = cursor.fetchone()
        count = row["count"] if row is not None else 0
        stats_table.add_row(table, f"{count:,}")

    console.print(stats_table)


def main() -> None:
    """
    Main function to orchestrate all database sanity checks.
    """

    load_dotenv(dotenv_path=ENV_PATH)

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

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

# this list defines the sanity checks
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
) -> bool:
    """
    Runs a single database check and prints the result.
    """

    console.print(f"🔎 Running check: [bold cyan]{title}[/bold cyan]...", end="")
    cursor.execute(query)
    result = cursor.fetchall()
    if failure_condition(result):
        console.print(" [bold red]❌ FAILED[/bold red]")
        console.print(f"    💬 Reason: {failure_message}")
        if result and result[0] and result[0].get("count", 0) > 0:
            console.print(f"    Result: {result}")
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
        "configuration_versions",
    ]

    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table};")
        row = cursor.fetchone()
        count = row["count"] if row is not None else 0
        stats_table.add_row(table, f"{count:,}")

    console.print(stats_table)


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
    all_checks_passed = True
    try:
        connection = get_db_connection(console)
        with connection.cursor() as cursor:
            for check in DB_CHECKS:
                passed = run_check(
                    cursor,
                    console,
                    title=check["title"],
                    query=check["query"],
                    failure_condition=check["failure_condition"],
                    failure_message=check["failure_message"],
                )
                if not passed:
                    all_checks_passed = False

            if all_checks_passed:
                console.print(
                    "\n[bold green]🎉 All critical sanity checks passed.[/bold green]\n"
                )
                display_summary_stats(cursor, console)
            else:
                console.print(
                    "\n[bold red]❌ One or more critical sanity checks failed.[/bold red]"
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

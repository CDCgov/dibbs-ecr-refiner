import os
import pathlib
import sys
from collections.abc import Callable

import psycopg
from dotenv import load_dotenv
from psycopg import Connection, Cursor
from rich.console import Console
from rich.table import Table


def get_db_connection(console: Console) -> Connection:
    """
    Constructs a DB connection string from environment variables and connects.
    """

    try:
        # construct the database URL from individual environment variables
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        dbname = os.getenv("POSTGRES_DB")
        port = os.getenv("POSTGRES_PORT")
        host = "localhost"

        if not all([user, password, dbname, port]):
            raise ValueError(
                "😓 Missing one or more required environment variables in .env file: ",
                "POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT",
            )

        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        return psycopg.connect(db_url, autocommit=True)

    except (psycopg.OperationalError, ValueError) as error:
        console.print(
            "[bold red]💥 FATAL: Could not connect to the database.[/bold red]\n",
            "Please ensure the database is running and all required environment variables are set correctly in the .env file.\n",
            f"💬 Error: {error}",
        )
        sys.exit(1)


def run_check(
    cursor: Cursor,
    console: Console,
    title: str,
    query: str,
    failure_condition: Callable[[list], bool],
    failure_message: str,
) -> bool:
    """
    A generic function to run a validation check against the database.
    """

    console.print(f"🔎 Running check: [bold cyan]{title}[/bold cyan]...", end="")
    cursor.execute(query)
    result = cursor.fetchall()

    if failure_condition(result):
        console.print(" [bold red]❌ FAILED[/bold red]")
        console.print(f"    💬 Reason: {failure_message}")
        if result and result[0]:
            console.print(f"    Result: {result}")
        return False
    else:
        console.print(" [bold green]✅ PASSED[/bold green]")
        return True


def display_summary_stats(cursor: Cursor, console: Console) -> None:
    """
    Displays a summary of row counts for key tables.
    """
    console.rule()
    console.print("\n[bold blue]📊 Database Summary Statistics[/bold blue]\n")
    stats_table = Table(title="Table Row Counts")
    stats_table.add_column("Table Name", style="cyan")
    stats_table.add_column("Row Count", style="magenta", justify="right")

    tables_to_check = [
        "tes_condition_groupers",
        "tes_reporting_spec_groupers",
        "tes_condition_grouper_references",
        "refinement_cache",
    ]

    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        row = cursor.fetchone()
        if row is not None:
            count = row[0]
        else:
            count = 0
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
    connection = None
    all_checks_passed = True
    try:
        connection = get_db_connection(console)
        with connection.cursor() as cursor:
            # critical checks...
            if not run_check(
                cursor,
                console,
                "No Orphaned References",
                """
                    SELECT COUNT(*)
                    FROM tes_condition_grouper_references ref
                    LEFT JOIN tes_reporting_spec_groupers child
                    ON ref.child_grouper_url = child.canonical_url AND ref.child_grouper_version = child.version
                    WHERE child.canonical_url IS NULL;
                """,
                lambda res: res[0][0] > 0,
                "Found references pointing to non-existent child groupers.",
            ):
                all_checks_passed = False

            if not run_check(
                cursor,
                console,
                "No Duplicate Condition Groupers",
                "SELECT COUNT(*) FROM (SELECT canonical_url, version, COUNT(*) FROM tes_condition_groupers GROUP BY canonical_url, version HAVING COUNT(*) > 1) as duplicates;",
                lambda res: res[0][0] > 0,
                "Found duplicate entries in tes_condition_groupers.",
            ):
                all_checks_passed = False

            if not run_check(
                cursor,
                console,
                "No Duplicate Reporting Spec Groupers",
                "SELECT COUNT(*) FROM (SELECT canonical_url, version, COUNT(*) FROM tes_reporting_spec_groupers GROUP BY canonical_url, version HAVING COUNT(*) > 1) as duplicates;",
                lambda res: res[0][0] > 0,
                "Found duplicate entries in tes_reporting_spec_groupers.",
            ):
                all_checks_passed = False

            if not run_check(
                cursor,
                console,
                "Refinement Cache Populated",
                "SELECT COUNT(*) FROM refinement_cache;",
                lambda res: res[0][0] == 0,
                "The refinement_cache table is empty, indicating triggers may not have fired.",
            ):
                all_checks_passed = False

            # summary
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

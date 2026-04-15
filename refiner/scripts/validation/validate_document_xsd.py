from pathlib import Path

from lxml import etree
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

BASE_DIR = Path(__file__).parent
SCHEMA_DIR = BASE_DIR / "cda-r2-schema"
ROOT_SCHEMA = SCHEMA_DIR / "infrastructure" / "cda" / "CDA_SDTC.xsd"

DATA_DIR = BASE_DIR.parent / "data" / "source-ecr-files"


def build_schema(console: Console) -> etree.XMLSchema | None:
    """
    Parse and compile the CDA R2 schema.

    lxml resolves all xs:include/xs:import paths relative to the root
    schema file's location, so the HL7 directory tree under cda-r2-schema/
    is sufficient — no custom resolver needed.

    Returns None and prints an error if schema compilation fails.
    """

    try:
        schema_doc = etree.parse(str(ROOT_SCHEMA))
        return etree.XMLSchema(schema_doc)
    except etree.XMLSchemaParseError as e:
        console.print(
            f"❌ Failed to compile CDA R2 schema: {e}",
            style="bold bright_red",
        )
        return None


def validate_xml_with_xsd(
    xml_path: Path, console: Console | None = None
) -> list[dict[str, str]]:
    """
    Validate a CDA document against the CDA R2 XSD schema set.

    Returns a list of validation issue dicts with keys:
        severity  - always "ERROR" for XSD violations
        message   - human-readable error description
        location  - line:column in the source document
        path      - lxml's element path at the error site

    Raises ValueError if the schema cannot be compiled.
    """

    if console is None:
        console = Console()

    schema = build_schema(console)
    if schema is None:
        raise ValueError("Could not compile CDA R2 schema.")

    try:
        doc = etree.parse(str(xml_path))
    except etree.XMLSyntaxError as e:
        console.print(f"❌ XML parse error: {e}", style="bold bright_red")
        return []

    schema.validate(doc)

    results = []
    for error in schema.error_log:
        results.append(
            {
                "severity": "ERROR",
                "message": error.message,
                "location": f"line {error.line}, col {error.column}",
                "path": error.path or "unknown",
            }
        )

    return results


def display_xsd_results(
    validation_results: list[dict[str, str]], console: Console
) -> None:
    """
    Render XSD validation errors in the same table style as schematron results.
    """

    table = Table(
        title="CDA R2 XSD Validation Report",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Severity", style="dim", width=10)
    table.add_column("Message", no_wrap=False)
    table.add_column("Location", no_wrap=False)
    table.add_column("XPath / Element", no_wrap=False)

    for result in validation_results:
        table.add_row(
            result["severity"],
            result["message"],
            result["location"],
            result["path"],
            style="bright_red",
        )

    console.print(table)


def display_xsd_summary(
    validation_results: list[dict[str, str]], console: Console
) -> None:
    """
    Display a summary panel matching the schematron validator's style.
    """

    error_count = len(validation_results)
    error_style = "bold red" if error_count else "bold green"

    summary_panel = Panel(
        f"[{error_style}]Total XSD Errors: {error_count}[/]",
        title="[bold]XSD Validation Summary[/bold]",
        border_style="gray70",
    )
    console.print(summary_panel)

    if error_count:
        console.print("\nXSD Validation FAILED", style="bold bright_red on white")
    else:
        console.print("\nXSD Validation Passed", style="bold green1")


def run_xsd_validation(xml_path: Path) -> None:
    """
    Orchestrate XSD validation for a single file and display results.
    """

    console = Console()
    console.print(f"Analyzing file: [bold]{xml_path.name}[/bold]")
    console.print(f"Schema root: [dim]{ROOT_SCHEMA.relative_to(BASE_DIR)}[/dim]\n")

    try:
        results = validate_xml_with_xsd(xml_path, console)
    except ValueError:
        console.print("XSD validation aborted.", style="bold bright_red")
        return

    if not results:
        console.print(
            Panel(
                "[bold green]✅ XSD Validation Passed: Document conforms to CDA R2 schema.[/bold green]"
            )
        )
        return

    display_xsd_results(results, console)
    display_xsd_summary(results, console)


def main() -> None:
    """
    Main function to select a file and run validation.
    """

    import subprocess

    console = Console()

    if not DATA_DIR.exists():
        console.print(
            f"[bold red]Error:[/bold red] Data directory '{DATA_DIR}' does not exist."
        )
        return

    files_in_dir = list(DATA_DIR.iterdir())
    if not files_in_dir:
        console.print(
            f"[bold yellow]Warning:[/bold yellow] Data directory '{DATA_DIR}' is empty."
        )
        return

    try:
        fzf_process = subprocess.run(
            [
                "fzf",
                "--prompt=Select a CDA XML file to validate: ",
                "--height=40%",
                "--layout=reverse",
            ],
            stdout=subprocess.PIPE,
            text=True,
            cwd=DATA_DIR,
            check=True,
        )
        selected_file = fzf_process.stdout.strip()

        if selected_file:
            run_xsd_validation(DATA_DIR / selected_file)
        else:
            console.print("No file selected.")

    except FileNotFoundError:
        console.print("Error: `fzf` not found. Please install fzf.", style="bold red")
    except subprocess.CalledProcessError:
        console.print("fzf exited without a selection.")
    except Exception as e:
        console.print(f"Unexpected error: {e}", style="bold red")


if __name__ == "__main__":
    main()

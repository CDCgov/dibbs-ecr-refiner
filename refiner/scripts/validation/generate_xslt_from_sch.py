import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from saxonche import PySaxonProcessor

# --- Configuration ---
BASE_DIR = Path(__file__).parent
SCHXSLT_PIPELINE_PATH = BASE_DIR / "schxslt" / "pipeline-for-svrl.xsl"


def generate_xslt_from_schematron(saxon_processor, sch_path, xslt_path):
    """
    Transforms a single Schematron .sch file to an .xslt file.
    Returns a dictionary with the status and any error message.
    """
    try:
        xslt_processor = saxon_processor.new_xslt30_processor()
        schxslt_executable = xslt_processor.compile_stylesheet(
            stylesheet_file=str(SCHXSLT_PIPELINE_PATH)
        )
        xslt_content = schxslt_executable.transform_to_string(source_file=str(sch_path))

        if xslt_content:
            xslt_path.write_text(xslt_content)
            return {"status": "Success", "error": None}
        else:
            return {"status": "Failure", "error": "Transformation produced no output."}

    except Exception as e:
        return {"status": "Failure", "error": str(e)}


def main():
    """
    Finds all .sch files in the validation subdirectories and generates
    the corresponding .xslt artifacts, displaying results in a rich table.
    """
    console = Console()
    start_time = time.time()

    console.print(
        Panel.fit(
            "[bold magenta]Schematron to XSLT Generator[/bold magenta]",
            border_style="green",
        )
    )

    schematron_files = sorted([p for p in BASE_DIR.rglob("*.sch") if p.is_file()])

    if not schematron_files:
        console.print(
            "[yellow]No Schematron (.sch) files found. Nothing to do.[/yellow]"
        )
        return

    console.print(f"Found {len(schematron_files)} Schematron file(s) to process...\n")

    results_table = Table(
        title="Transformation Results",
        header_style="bold blue",
        show_lines=True,
        border_style="gray70",
    )
    results_table.add_column("Status", justify="center", width=8)
    results_table.add_column("Standard", style="cyan", no_wrap=True)
    results_table.add_column("Output File", style="green", no_wrap=False)

    all_results = []
    with PySaxonProcessor(license=False) as processor:
        for sch_file in schematron_files:
            xslt_file = sch_file.with_suffix(".xslt")
            result = generate_xslt_from_schematron(processor, sch_file, xslt_file)
            all_results.append(result)

            status_emoji = "✅" if result["status"] == "Success" else "❌"
            status_color = "green" if result["status"] == "Success" else "red"

            results_table.add_row(
                f"[{status_color}]{status_emoji}[/]",
                sch_file.parent.name,
                str(xslt_file.relative_to(BASE_DIR)),
            )
            if result["error"]:
                results_table.add_row(
                    "", "[dim]Error[/dim]", f"[red]{result['error']}[/red]"
                )

    console.print(results_table)

    # --- Summary Panel ---
    end_time = time.time()
    success_count = sum(1 for r in all_results if r["status"] == "Success")
    failure_count = len(all_results) - success_count

    summary_color = "green" if failure_count == 0 else "red"
    summary_text = (
        f"✅ [bold]All {success_count} files generated successfully![/bold]\n"
        if failure_count == 0
        else f"❌ [bold]Completed with {failure_count} failure(s).[/bold]\n"
    )
    summary_text += f"Total time: {end_time - start_time:.2f} seconds"

    console.print(
        Panel(
            summary_text,
            title="[bold]Summary[/bold]",
            border_style=summary_color,
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()

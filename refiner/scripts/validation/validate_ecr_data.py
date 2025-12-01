import subprocess
from pathlib import Path

from lxml import etree
from lxml.etree import _Element
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from saxonche import PySaxonProcessor

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data" / "source-ecr-files"
VALIDATION_ASSETS_DIR = BASE_DIR

# in order to know which xslt to use, we need to look at the main document level OID and its extension (date)
# this tells us which transformed xslt to use in our validation related work
STANDARDS_MAP = {
    # eICR versions
    "2.16.840.1.113883.10.20.15.2": {
        "name": "eICR",
        "versions": {
            "2016-12-01": {
                "version_name": "STU 1.1.1",
                "path": VALIDATION_ASSETS_DIR
                / "eicr-cda-stu-1.1.1"
                / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xslt",
            },
            "2021-01-01": {
                "version_name": "STU 3.0",
                "path": VALIDATION_ASSETS_DIR
                / "eicr-cda-stu-3.0"
                / "CDAR2_IG_PHCASERPT_R2_D3_SCHEMATRON.xslt",
            },
            "2022-05-01": {
                "version_name": "STU 3.1.1",
                "path": VALIDATION_ASSETS_DIR
                / "eicr-cda-stu-3.1.1"
                / "CDAR2_IG_PHCASERPT_R2_STU3.1.1_SCHEMATRON.xslt",
            },
        },
    },
    # RR versions (so far just the one 1.1 version)
    "2.16.840.1.113883.10.20.15.2.1.2": {
        "name": "RR",
        "versions": {
            "2017-04-01": {
                "version_name": "STU 1.1.0",
                "path": VALIDATION_ASSETS_DIR
                / "rr-cda-stu-1.1.0"
                / "CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xslt",
            }
        },
    },
}


def get_document_template_info(
    root: _Element, nsmap: dict[str, str]
) -> tuple[str, str] | tuple[None, None]:
    """
    Finds the most specific templateId that matches our known standards.
    """

    # iterate through our known standards (the keys of STANDARDS_MAP)
    for standard_oid in STANDARDS_MAP:
        # for each standard, build a very specific XPath to find ONLY that templateId
        xpath_query = f"hl7:templateId[@root='{standard_oid}']"
        template_id_element = root.xpath(xpath_query, namespaces=nsmap)

        # if we find a match for this specific standard OID
        if template_id_element:
            # get its extension and return it immediately
            # this prioritizes the OIDs in our map over any others
            extension = template_id_element[0].get("extension", "none")
            return standard_oid, extension

    # if we loop through all our known standards and find none, return None
    return None, None


def determine_validation_path(xml_path: Path) -> tuple[str, Path] | tuple[None, None]:
    """
    Determine eICR/RR version and return its file path.

    Determines the document type and version using its templateId, then returns
    the name and the correct path to the validation XSLT file.
    """

    console = Console()
    console.print(f"Analyzing file: {xml_path.name}")

    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        nsmap = {"hl7": "urn:hl7-org:v3"}

        root_oid, extension = get_document_template_info(root, nsmap)

        if not root_oid:
            console.print(
                "❌ Could not find a recognizable eICR or RR document-level templateId.",
                style="bold bright_red",
            )
            return None, None

        if root_oid in STANDARDS_MAP:
            standard_family = STANDARDS_MAP[root_oid]

            if extension in standard_family["versions"]:
                version_info = standard_family["versions"][extension]
                doc_type_name = standard_family["name"]
                version_name = version_info["version_name"]
                xslt_path = version_info["path"]

                console.print(
                    f"✅ Document: [bold]{doc_type_name} {version_name}[/bold] (root: {root_oid}, ext: {extension})",
                    style="green1",
                )
                return doc_type_name, xslt_path
            else:
                console.print(
                    f"❌ Found standard with root '{root_oid}' but its extension '{extension}' is unknown.",
                    style="bold bright_red",
                )
                return None, None
        else:
            console.print(
                f"❌ Unknown document standard with root OID: {root_oid}",
                style="bold bright_red",
            )
            return None, None

    except Exception as e:
        console.print(
            f"❌ Error determining document type: {e}", style="bold bright_red"
        )
        return None, None


def parse_svrl(svrl_result_string: str) -> list[dict[str, str]]:
    """
    Parse the SVRL XML string and extract validation results.
    """

    svrl_doc = etree.fromstring(svrl_result_string.encode("utf-8"))
    ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
    results = []

    for assertion in svrl_doc.xpath(".//svrl:failed-assert", namespaces=ns):
        message = assertion.findtext("svrl:text", namespaces=ns).strip() or "No message"

        role = assertion.get("role", "").upper()
        if role in ["FATAL", "ERROR"]:
            severity = "ERROR"
        elif role == "WARN":
            severity = "WARNING"
        elif "SHOULD" in message:
            severity = "WARNING"
        else:
            severity = "ERROR"

        results.append(
            {
                "severity": severity,
                "message": message,
                "location": assertion.get("location", "No location"),
                "test": assertion.get("test", "No test"),
            }
        )
    return results


def display_svrl_results(
    validation_results: list[dict[str, str]], console: Console
) -> None:
    """
    Display validation results in a rich table with text wrapping.
    """

    table = Table(
        title="Schematron Validation Report",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Severity", style="dim", width=10)
    table.add_column("Message", no_wrap=False)
    table.add_column("Location (XPath)", no_wrap=False)

    for result in sorted(validation_results, key=lambda x: x["severity"]):
        severity = result["severity"]
        style = (
            "bright_red"
            if severity in ["ERROR", "FATAL"]
            else "orange1"
            if severity == "WARNING"
            else "blue"
        )
        table.add_row(severity, result["message"], result["location"], style=style)

    console.print(table)


def display_summary(validation_results: list[dict[str, str]], console: Console) -> None:
    """
    Display a summary of errors and warnings.
    """

    errors = [
        res for res in validation_results if res["severity"] in ["ERROR", "FATAL"]
    ]
    warnings = [res for res in validation_results if res["severity"] == "WARNING"]

    error_style = "bold red" if errors else "bold green"
    warning_style = "bold yellow" if warnings else "bold green"

    summary_panel = Panel(
        f"[{error_style}]Total Errors: {len(errors)}[/]\n"
        f"[{warning_style}]Total Warnings: {len(warnings)}[/]",
        title="[bold]Summary[/bold]",
        border_style="gray70",
    )
    console.print(summary_panel)

    if len(errors) > 0:
        console.print("\nValidation FAILED", style="bold bright_red on white")
    elif len(warnings) > 0:
        console.print("\nValidation Passed with Warnings", style="bold yellow")
    else:
        console.print("\nValidation Passed", style="bold green1")


def validate_xml_with_schematron(xml_path: Path) -> None:
    """
    Orchestrates the validation process for a single XML file.
    """

    console = Console()
    doc_type, xslt_path = determine_validation_path(xml_path)
    if not doc_type:
        console.print("Validation aborted.", style="bold bright_red")
        return

    console.print(f"Using stylesheet: {xslt_path.relative_to(BASE_DIR)}")

    with PySaxonProcessor(license=False) as processor:
        try:
            xslt_processor = processor.new_xslt30_processor()
            executable = xslt_processor.compile_stylesheet(
                stylesheet_file=str(xslt_path)
            )
            console.print("Stylesheet compiled successfully.", style="green1")

            svrl_output_string = executable.transform_to_string(
                source_file=str(xml_path)
            )

            if not svrl_output_string:
                console.print(
                    "Transformation produced no output. The file may be valid or the stylesheet may be misconfigured.",
                    style="bold orange1",
                )
                return

            validation_results = parse_svrl(svrl_output_string)

            if not validation_results:
                console.print(
                    Panel(
                        "[bold green]✅ Validation Passed: No errors or warnings found![/bold green]"
                    )
                )
                return

            display_svrl_results(validation_results, console)
            display_summary(validation_results, console)

        except Exception as e:
            console.print(
                f"An error occurred during Saxon processing: {e}",
                style="bold bright_red",
            )


def main() -> None:
    """
    Main function to select a file and run validation.
    """

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
                "--prompt=Select an XML file to validate: ",
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
            xml_to_validate = DATA_DIR / selected_file
            validate_xml_with_schematron(xml_to_validate)
        else:
            print("No file selected.")

    except FileNotFoundError:
        print("Error: `fzf` command not found. Please install fzf to use this script.")
    except subprocess.CalledProcessError:
        print("fzf was exited without a selection.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

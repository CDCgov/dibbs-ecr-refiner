import subprocess
from pathlib import Path
from typing import Any

from eicr_trigger_codes import EICR_TRIGGER_CODES
from lxml import etree
from lxml.etree import _Element
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

SOURCE_DIR: Path = Path(__file__).parent.resolve()

EICR_VERSION_MAP: dict[str, str] = {
    "2016-12-01": "1.1",
    "2021-01-01": "3.1",
    "2022-05-01": "3.1.1",
}


def pick_xml_file() -> Path | None:
    """
    Use fzf to select an XML file from the current directory.
    """

    files = [
        f.name
        for f in SOURCE_DIR.iterdir()
        if f.is_file() and f.suffix.lower() == ".xml"
    ]
    if not files:
        Console().print("[red]No XML files in directory.[/red]")
        return None
    try:
        fzf_process = subprocess.run(
            [
                "fzf",
                "--prompt=Select an eICR XML file: ",
                "--height=40%",
                "--layout=reverse",
            ],
            input="\n".join(files),
            stdout=subprocess.PIPE,
            text=True,
            cwd=SOURCE_DIR,
            check=True,
        )
        selected_file = fzf_process.stdout.strip()
        if selected_file:
            return SOURCE_DIR / selected_file
        else:
            Console().print("[yellow]No file selected.[/yellow]")
            return None
    except Exception as e:
        Console().print(f"[red]fzf error: {e}[/red]")
        return None


def get_eicr_version(root: _Element, ns: dict) -> str | None:
    """
    Determine the eICR version from the document's templateId.
    """

    template_id = root.find(
        'hl7:templateId[@root="2.16.840.1.113883.10.20.15.2"]', namespaces=ns
    )
    if template_id is not None:
        version_date = template_id.get("extension")
        if version_date and version_date in EICR_VERSION_MAP:
            return EICR_VERSION_MAP[version_date]
    return None


def get_section_summary(section: _Element, ns: dict) -> tuple[str, str]:
    """
    Extract the LOINC code and title from a section element.
    """

    code = section.find("hl7:code", namespaces=ns)
    loinc = (
        code.get("code")
        if code is not None and code.get("code")
        else "(no LOINC code found)"
    )
    title_elt = section.find("hl7:title", namespaces=ns)
    title = (
        title_elt.text.strip()
        if title_elt is not None and title_elt.text
        else "(no title found)"
    )
    return loinc, title


def get_trigger_element(
    section: _Element, trigger_oids: dict[str, Any], ns: dict
) -> tuple[_Element | None, dict[str, Any] | None]:
    """
    Find the first element in a section that contains a trigger code template OID.
    """

    for elem in section.iter():
        for tmpl in elem.findall("hl7:templateId", namespaces=ns):
            root = tmpl.get("root")
            ext = tmpl.get("extension")
            oid_with_ext = f"{root}:{ext}" if ext else root
            if oid_with_ext in trigger_oids:
                trigger_details = trigger_oids[oid_with_ext]
                return elem, trigger_details
    return None, None


def main():
    console = Console()
    xml_path = pick_xml_file()
    if not xml_path:
        return

    ns = {"hl7": "urn:hl7-org:v3"}
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
    except Exception as e:
        console.print(f"[red]Error parsing XML: {e}[/red]")
        return

    version = get_eicr_version(root, ns)
    if not version:
        console.print("[red]Could not determine eICR version from the file.[/red]")
        return

    console.print(
        f"\n📄 [bold]File:[/bold] [blue]{xml_path.name}[/blue]   "
        f"🏷️ [bold]Detected Version:[/bold] [yellow]{version}[/yellow]\n"
    )
    version_config = EICR_TRIGGER_CODES.get(version, {})

    sections = root.findall(".//hl7:section", namespaces=ns)
    if not sections:
        console.print("[yellow]No <section> elements found in document.[/yellow]")
        return

    for idx, section in enumerate(sections, 1):
        loinc, title = get_section_summary(section, ns)
        section_config = version_config.get(loinc)

        if section_config:
            trigger_oids_to_find = section_config.get("trigger_codes", {})
            trigger_elem, trigger_details = get_trigger_element(
                section, trigger_oids_to_find, ns
            )
            section_display_name = section_config.get("display", title)
        else:
            trigger_elem, trigger_details = None, None
            section_display_name = title

        header = f"[bold]{idx}. LOINC:[/bold] [green]{loinc:<10}[/green] [bold]Section:[/bold] [magenta]{section_display_name}[/magenta]"

        if trigger_elem is not None and trigger_details:
            emoji = "🟢"
            status = Text.from_markup(
                f"[bold bright_green]TRIGGER FOUND![/bold bright_green] "
                f"✨ [dim]'{trigger_details.get('display')}'[/dim]"
            )
            xml_preview = Syntax(
                etree.tostring(trigger_elem, pretty_print=True, encoding="unicode"),
                "xml",
                theme="dracula",
                line_numbers=True,
            )
            panel = Panel(xml_preview, border_style="cyan")
        else:
            emoji = "🔘"
            status = Text("No trigger code template OID found.", style="dim")
            panel = None

        console.rule(style="grey50")
        console.print(f"{emoji} {header}\n{status}")

        if panel:
            console.print(panel)

    console.rule("[bold cyan]Analysis Complete[/bold cyan]")


if __name__ == "__main__":
    main()

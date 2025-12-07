import subprocess
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Final

from eicr_trigger_codes import EICR_TRIGGER_CODES
from lxml import etree
from lxml.etree import _Element
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

# namespace map of:
# prefix -> uri
type NamespaceMap = dict[str, str]

SOURCE_DIR: Final[Path] = Path(__file__).parent.resolve()

EICR_VERSION_MAP: Final[dict[str, str]] = {
    "2016-12-01": "1.1",
    "2021-01-01": "3.1",
    "2022-05-01": "3.1.1",
}

RR_DETERMINATION_CODES: Final[dict[str, str]] = {
    "RRVS1": "Reportable",
    "RRVS2": "May be reportable",
    "RRVS3": "Not reportable",
    "RRVS4": "No rule met",
}

NAMESPACES: Final[NamespaceMap] = {
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "voc": "http://www.lantanagroup.com/voc",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


def _fzf_select(console: Console, prompt: str, files: list[str]) -> Path | None:
    """
    Helper to run fzf selection.
    """

    try:
        process = subprocess.run(
            [
                "fzf",
                f"--prompt={prompt}",
                "--height=40%",
                "--layout=reverse",
            ],
            input="\n".join(files),
            stdout=subprocess.PIPE,
            text=True,
            cwd=SOURCE_DIR,
            check=True,
        )
        if selected := process.stdout.strip():
            return SOURCE_DIR / selected
    except subprocess.CalledProcessError:
        # fzf returns non-zero if cancelled (ESC)
        pass
    except Exception as e:
        console.print(f"[red]❌ fzf error: {e}[/red]")

    return None


def pick_xml_files(console: Console) -> tuple[Path | None, Path | None]:
    """
    Use fzf to select an eICR and an RR XML file.
    """

    files = [
        f.name
        for f in SOURCE_DIR.iterdir()
        if f.is_file() and f.suffix.lower() == ".xml"
    ]

    if not files:
        console.print("[red]❌ No XML files in directory.[/red]")
        return None, None

    eicr = _fzf_select(console, "Select an eICR XML file: ", files)
    if not eicr:
        console.print("[yellow]⚠️ No eICR file selected.[/yellow]")
        return None, None

    rr = _fzf_select(console, "Select the corresponding RR XML file: ", files)
    if not rr:
        console.print("[yellow]⚠️ No RR file selected.[/yellow]")
        return None, None

    return eicr, rr


def get_eicr_version(root: _Element, ns: NamespaceMap) -> str | None:
    """
    Find out which version of the eICR spec applies to the document.
    """

    if (
        template_id := root.find(
            'cda:templateId[@root="2.16.840.1.113883.10.20.15.2"]', namespaces=ns
        )
    ) is not None:
        if (version_date := template_id.get("extension")) in EICR_VERSION_MAP:
            return EICR_VERSION_MAP[version_date]
    return None


def display_eicr_details(
    console: Console, root: _Element, version: str, ns: NamespaceMap
) -> int:
    """
    Display section-by-section trigger details.
    """

    console.rule("[bold cyan]⚡ eICR Trigger Analysis[/bold cyan]", style="cyan")

    trigger_count = 0
    version_config = EICR_TRIGGER_CODES.get(version, {})
    sections = root.findall(".//cda:section", namespaces=ns)

    for idx, section in enumerate(sections, 1):
        code_element = section.find("cda:code", namespaces=ns)
        loinc = code_element.get("code") if code_element is not None else "(no LOINC)"

        # use .get chaining for safer access
        section_config = version_config.get(loinc, {})
        display_name = section_config.get("display", "Unknown Section")
        trigger_oids = section_config.get("trigger_codes", {})

        header = (
            f"[bold]{idx}. LOINC:[/bold] [green]{loinc:<10}[/green] "
            f"[bold]Section:[/bold] [magenta]{display_name}[/magenta]"
        )

        # use a generator to find the first match
        match_found = None

        if trigger_oids:
            # create a generator of (element, template_id) pairs
            candidates = (
                (elem, tmpl)
                for elem in section.iter()
                for tmpl in elem.findall("cda:templateId", namespaces=ns)
            )

            # find first match where OID is in trigger list
            match_found = next(
                (
                    # the output/payload
                    (elem, tmpl, f"{tmpl.get('root')}:{tmpl.get('extension')}")
                    # the loop/source
                    for elem, tmpl in candidates
                    # the filter
                    if f"{tmpl.get('root')}:{tmpl.get('extension')}" in trigger_oids
                ),
                # the fallback
                None,
            )

        if match_found:
            elem, _, oid_key = match_found
            trigger_count += 1
            details = trigger_oids[oid_key]

            status = Text.from_markup(
                f"[bold bright_green]TRIGGER FOUND![/bold bright_green] "
                f"✨ [dim]'{details.get('display')}'[/dim]"
            )
            console.print(f"🟢 {header}\n{status}")

            xml_preview = Syntax(
                etree.tostring(elem, pretty_print=True, encoding="unicode"),
                "xml",
                theme="dracula",
                line_numbers=True,
            )
            console.print(Panel(xml_preview, border_style="cyan"))
        else:
            status = Text("No trigger code template OID found.", style="dim")
            console.print(f"🔘 {header}\n{status}")

        console.rule(style="grey50")

    return trigger_count


def display_rr_details(console: Console, root: _Element, ns: NamespaceMap) -> Counter:
    """
    Display pruned 'Relevant Reportable Condition' block.
    """

    console.rule("[bold cyan]🔍 RR Determination Analysis[/bold cyan]", style="cyan")
    determinations: Counter = Counter()

    condition_observations = root.xpath(
        ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12']]",
        namespaces=ns,
    )

    if not condition_observations:
        console.print(
            "⚠️ No 'Relevant Reportable Condition' observations found.", style="yellow"
        )
        return determinations

    for idx, obs in enumerate(condition_observations, 1):
        if (snomed_val := obs.find("cda:value", namespaces=ns)) is None:
            continue

        snomed_code = snomed_val.get("code", "N/A")
        snomed_display = snomed_val.get("displayName", "N/A")
        header = f"[bold]{idx}. Condition:[/bold] [green]{snomed_display}[/green] ([dim]SNOMED: {snomed_code}[/dim])"

        rr1_value = obs.xpath(
            ".//cda:observation[cda:code/@code='RR1']/cda:value", namespaces=ns
        )

        if rr1_value:
            status_code = rr1_value[0].get("code")
            if status_code:
                determinations[status_code] += 1

            status_display = RR_DETERMINATION_CODES.get(status_code, "Unknown")

            jurisdiction_xpath = ".//cda:participantRole[cda:code/@code='RR7' or cda:code/@code='RR12']/cda:id/@extension"
            jurisdictions = obs.xpath(jurisdiction_xpath, namespaces=ns)

            jurisdiction_text = (
                f'\n[bold]Jurisdiction:[/bold] [yellow]"{jurisdictions[0]}"[/yellow]'
                if jurisdictions
                else ""
            )

            status = Text.from_markup(
                f"[bold bright_green]DETERMINATION FOUND![/bold bright_green] "
                f"✨ [dim]'{status_display} ({status_code})'[/dim]{jurisdiction_text}"
            )
            console.print(f"🟢 {header}\n{status}")

            # prune for display
            pruned_obs = deepcopy(obs)
            for entry_relationship in pruned_obs.findall("cda:entryRelationship", ns):
                pruned_obs.remove(entry_relationship)

            xml_preview = Syntax(
                etree.tostring(pruned_obs, pretty_print=True, encoding="unicode"),
                "xml",
                theme="dracula",
                line_numbers=True,
            )
            console.print(Panel(xml_preview, border_style="cyan"))
        else:
            console.print(f"🔘 {header}\n[dim]No RR1 determination found.[/dim]")

        console.rule(style="grey50")

    return determinations


def main():
    console = Console()

    if not (files := pick_xml_files(console)):
        return

    # unpack safe because pick_xml_files returns tuple of 2 or None/None
    eicr_path, rr_path = files
    if not eicr_path or not rr_path:
        return

    # process eicr
    try:
        eicr_root = etree.parse(str(eicr_path)).getroot()
        if not (eicr_version := get_eicr_version(eicr_root, NAMESPACES)):
            console.print(
                f"[red]❌ Could not determine eICR version from {eicr_path.name}.[/red]"
            )
            return

        console.print(
            f"\n📄 [bold]eICR File:[/bold] [blue]{eicr_path.name}[/blue]   "
            f"🏷️ [bold]Detected Version:[/bold] [yellow]{eicr_version}[/yellow]\n"
        )
        total_triggers = display_eicr_details(
            console, eicr_root, eicr_version, NAMESPACES
        )
    except Exception as e:
        console.print(f"[red]❌ Error processing eICR file: {e}[/red]")
        return

    # process rr
    try:
        rr_root = etree.parse(str(rr_path)).getroot()
        console.print(f"\n📄 [bold]RR File:[/bold] [blue]{rr_path.name}[/blue]\n")
        rr_counts = display_rr_details(console, rr_root, NAMESPACES)
    except Exception as e:
        console.print(f"[red]❌ Error processing RR file: {e}[/red]")
        return

    # summary table
    summary_table = Table(box=None, padding=(0, 1))
    summary_table.add_column("Category", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="magenta", justify="right")

    summary_table.add_row(
        Text("Total Trigger Codes Found", style="bold"), str(total_triggers)
    )
    summary_table.add_row("─" * 30, "─" * 10, end_section=True)
    summary_table.add_row(Text("Total RR Determinations", style="bold underline"), "")

    if rr_counts:
        for code, count in sorted(rr_counts.items()):
            display_name = RR_DETERMINATION_CODES.get(code, "Unknown")
            summary_table.add_row(f"  {display_name} ({code})", str(count))
    else:
        summary_table.add_row("  No determinations found", "0")

    console.print(
        Panel(
            summary_table,
            title="[bold green]📋 Analysis Summary[/bold green]",
            border_style="green",
            expand=False,
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()

from pathlib import Path

from lxml import etree

# this loader assumes it lives in the 'fixtures' directory.
FIXTURE_DIR = Path(__file__).parent


def load_fixture_str(path_from_fixture_dir: str) -> str:
    """
    Loads a fixture file as a raw string.
    """

    file_path: Path = FIXTURE_DIR / path_from_fixture_dir

    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")

    with open(file_path, encoding="utf-8") as file:
        return file.read()


def load_fixture_xml(path_from_fixture_dir: str) -> etree._Element:
    """
    Loads and parses an XML fixture file into an `lxml` `_Element`.
    """

    xml_string: bytes = load_fixture_str(path_from_fixture_dir).encode("utf-8")

    # using a parser that removes blank text for cleaner test assertions
    parser = etree.XMLParser(remove_blank_text=True)

    return etree.fromstring(xml_string, parser=parser)

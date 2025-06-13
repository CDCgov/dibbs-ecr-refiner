import json
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from chardet import detect
from lxml import etree
from lxml.etree import _Element

from ..core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ..core.models.types import FileUpload, XMLFiles


def get_asset_path(*paths: str) -> Path:
    """
    Get the full path to an asset file or directory.

    Args:
        *paths: Variable number of path segments to join after 'assets'
               e.g., get_asset_path('demo', 'monmothma.zip')
               or get_asset_path('refiner_details.json')

    Returns:
        Path: Full path to the requested asset

    Example:
        >>> get_asset_path('demo', 'monmothma.zip')
        Path('/path/to/project/assets/demo/monmothma.zip')
        >>> get_asset_path('refiner_details.json')
        Path('/path/to/project/assets/refiner_details.json')
    """

    base_path = Path(__file__).parent.parent.parent / "assets"
    return base_path.joinpath(*paths)


def read_json_asset(filename: str) -> dict:
    """
    Read and parse a JSON file from the assets directory.
    """

    with get_asset_path(filename).open() as f:
        return json.load(f)


def parse_xml(xml_content: str | bytes) -> _Element:
    """
    Parse XML content into an element tree.

    Args:
        xml_content: XML content as string or bytes

    Returns:
        _Element: Parsed XML element tree

    Raises:
        XMLValidationError: If XML is invalid or empty
    """

    if xml_content is None:
        raise XMLValidationError(
            message="XML content cannot be empty",
            details={"provided_content": None},
        )
    # This handles empty string/bytes
    if not xml_content:
        raise XMLValidationError(
            message="XML content cannot be empty",
            details={"provided_length": len(xml_content)},
        )

    try:
        # we can use remove_blank_text=True if we want a more aggressive removal of whitespace
        parser = etree.XMLParser()
        if isinstance(xml_content, str):
            xml_content = xml_content.encode("utf-8")
        return etree.fromstring(xml_content, parser=parser)
    except etree.ParseError as e:
        raise XMLValidationError(
            message="Failed to parse XML",
            details={
                "error": str(e),
                "line": getattr(e, "line", None),
                "column": getattr(e, "column", None),
            },
        )


async def read_xml_zip(file: FileUpload) -> XMLFiles:
    """
    Read XML files from a ZIP archive.
    """
    try:
        zip_bytes = await file.read()
        zip_stream = BytesIO(zip_bytes)

        with ZipFile(zip_stream, "r") as z:
            eicr_xml = None
            rr_xml = None

            for filename in z.namelist():
                # skip macOS resource fork files
                if filename.startswith("__MACOSX/") or filename.startswith("._"):
                    continue

                content = z.read(filename)
                encoding = detect(content)["encoding"] or "utf-8"
                decoded = content.decode(encoding)

                if filename.endswith("CDA_eICR.xml"):
                    eicr_xml = decoded
                elif filename.endswith("CDA_RR.xml"):
                    rr_xml = decoded

            if not eicr_xml:
                raise ZipValidationError(
                    message="Required file CDA_eICR.xml not found in .zip.",
                    details={
                        "files_found": [
                            f
                            for f in z.namelist()
                            if not (f.startswith("__MACOSX/") or f.startswith("._"))
                        ],
                        "required_files": ["CDA_eICR.xml", "CDA_RR.xml"],
                    },
                )

            if not rr_xml:
                raise ZipValidationError(
                    message="Required file CDA_RR.xml not found in .zip.",
                    details={
                        "files_found": [
                            f
                            for f in z.namelist()
                            if not (f.startswith("__MACOSX/") or f.startswith("._"))
                        ],
                        "required_files": ["CDA_eICR.xml", "CDA_RR.xml"],
                    },
                )

            return XMLFiles(eicr_xml, rr_xml)

    except BadZipFile:
        raise ZipValidationError(
            message="Invalid ZIP file provided",
            details={
                "error": "File is not a valid ZIP archive",
                "requirements": "ZIP must contain CDA_eICR.xml and CDA_RR.xml files",
            },
        )
    except ZipValidationError:
        # re-raise ZipValidationError without wrapping it
        raise
    except Exception as e:
        raise FileProcessingError(
            message="Failed to process ZIP file", details={"error": str(e)}
        )

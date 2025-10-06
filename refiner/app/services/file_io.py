import io
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, ZipInfo

from chardet import detect
from lxml import etree
from lxml.etree import _Element

from ..core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ..core.models.types import FileUpload, XMLFiles

MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50 MB


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


def create_split_condition_filename(condition_name: str, condition_code: str) -> str:
    """
    Create a standard file name from a condition's name and code.

    Args:
        condition_name (str): Name of a condition
        condition_code (str): Code of a condition

    Returns:
        str: Standard XML file name
    """

    safe_name = condition_name.replace(" ", "_").replace("/", "_")
    filename = f"CDA_eICR_{condition_code}_{safe_name}.xml"

    return filename


def create_refined_ecr_zip_in_memory(
    *,
    files: list[tuple[str, str]],
) -> tuple[str, io.BytesIO]:
    """
    Create a zip archive containing all provided (filename, content) pairs.

    Args:
        files (list[tuple[str, str]]): List of tuples [(filename, content)], content must be a string.

    Returns:
        (filename, buffer)
    """
    token = str(uuid4())
    zip_filename = f"{token}_refined_ecr.zip"
    zip_buffer = io.BytesIO()

    with ZipFile(zip_buffer, "w") as zf:
        for filename, content in files:
            zf.writestr(filename, content)

    zip_buffer.seek(0)
    return zip_filename, zip_buffer


def _decode_file(filename: str, zipfile: ZipFile) -> str:
    """
    Reads and decodes the contents of a file within a ZIP archive.

    This function detects the file's character encoding and decodes it into a string.

    Args:
        filename (str): The name of the file inside the ZIP archive to read.
        zipfile (ZipFile): The opened ZIP archive containing the file.

    Returns:
        str: The decoded contents of the file as a string.
    """
    content = zipfile.read(filename)
    encoding = detect(content)["encoding"] or "utf-8"
    decoded = content.decode(encoding)
    return decoded


def _is_valid_uncompressed_size(info: list[ZipInfo]) -> bool:
    """
    Determines whether the total uncompressed size of the ZIP contents is within the allowed limit.

    Args:
        info (list[ZipInfo]): List of file metadata entries from the ZIP archive.

    Returns:
        bool: True if the total uncompressed size is less than 50 MB; otherwise, False.
    """
    return sum(zinfo.file_size for zinfo in info) < MAX_UNCOMPRESSED_SIZE


async def read_xml_zip(file: FileUpload) -> XMLFiles:
    """
    Read XML files from a ZIP archive.
    """
    try:
        file_content = await file.read()
        with ZipFile(BytesIO(file_content), "r") as zf:
            eicr_xml = None
            rr_xml = None

            if not _is_valid_uncompressed_size(zf.infolist()):
                raise ZipValidationError(
                    message="Uncompressed .zip file must not exceed 50MB in size."
                )

            namelist = zf.namelist()
            for filename in namelist:
                # skip files we don't need
                if (
                    filename.startswith("__MACOSX/")
                    or filename.startswith("._")
                    or not filename.endswith(("CDA_eICR.xml", "CDA_RR.xml"))
                ):
                    continue

                if filename.endswith("CDA_eICR.xml"):
                    eicr_xml = _decode_file(filename, zf)
                elif filename.endswith("CDA_RR.xml"):
                    rr_xml = _decode_file(filename, zf)

            if not eicr_xml:
                raise ZipValidationError(
                    message="Required file CDA_eICR.xml not found in .zip file.",
                    details={
                        "files_found": [
                            f
                            for f in namelist
                            if not (f.startswith("__MACOSX/") or f.startswith("._"))
                        ],
                        "required_files": ["CDA_eICR.xml", "CDA_RR.xml"],
                    },
                )

            if not rr_xml:
                raise ZipValidationError(
                    message="Required file CDA_RR.xml not found in .zip file.",
                    details={
                        "files_found": [
                            f
                            for f in namelist
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

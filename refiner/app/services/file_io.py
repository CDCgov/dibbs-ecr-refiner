import io
import time
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from chardet import detect
from lxml import etree
from lxml.etree import _Element

from app.services.conditions.naming import get_computed_condition_name

from ..core.exceptions import (
    FileProcessingError,
    XMLValidationError,
    ZipSizeError,
    ZipValidationError,
)
from ..core.models.types import FileUpload, XMLFiles


@dataclass
class ZipFileItem:
    """
    Represents an object to add to a ZipFilePackage.
    """

    file_name: str
    file_content: str


class ZipFilePackage:
    """
    Represents a collection of documents to use for creating a zip file package.
    """

    def __init__(self, name: str) -> None:
        """
        ZipFilePackage constructor.
        """
        self._name = name
        self._packaged_items: list[ZipFileItem] = []

    def get_name(self) -> str:
        """
        Get the name of the zip package.
        """
        return self._name

    def add(self, item: ZipFileItem) -> None:
        """
        Adds a zipped item to the package.

        Args:
            item (ZippedItem): The item to add to the package
        """
        if item.file_name in [i.file_name for i in self._packaged_items]:
            raise ValueError(
                f"Conflicting ZipFileItem name during packaging: {item.file_name}. Names must be unique."
            )
        self._packaged_items.append(item)

    def get_items(self) -> list[ZipFileItem]:
        """
        Gets the zip package.

        Returns:
            list[ZippedItem]: All items in the zip package.
        """
        return list(self._packaged_items)

    def iter_chunks(self) -> Iterator[bytes]:
        """
        Yields the zip file contents as chunks. Useful for usage with a StreamingResponse.
        """
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
            for item in self._packaged_items:
                zf.writestr(item.file_name, item.file_content)
        yield buffer.getvalue()


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


@dataclass
class RefinedFileName:
    """
    File name object.
    """

    eicr_xml_file_name: str
    eicr_html_file_name: str
    rr_xml_file_name: str


def create_refined_file_names(
    condition_name: str,
) -> RefinedFileName:
    """
    Create file names for a refined condition given the name and code.

    Args:
        jurisdiction_id: the jurisdiction
        condition_name (str): Name of a condition

    Returns:
        RefinedFileName: Object with all required file names for packaging
    """
    computed_name = get_computed_condition_name(condition_name=condition_name)
    eicr_base_name = f"CDA_eICR_{computed_name}"

    return RefinedFileName(
        eicr_xml_file_name=f"{eicr_base_name}.xml",
        eicr_html_file_name=f"{eicr_base_name}.html",
        rr_xml_file_name=f"CDA_RR_{computed_name}.xml",
    )


def create_refined_ecr_zip_in_memory(
    *,
    zip_package: ZipFilePackage,
) -> tuple[str, io.BytesIO]:
    """
    Create a zip archive containing all provided (filename, content) pairs (content may be str or bytes).

    Args:
        zip_package (ZipFilePackage): A constructed file package

    Returns:
        (filename, buffer)

    Notes:
        - If content is bytes, it is written as-is.
        - If content is str, it is encoded as UTF-8 before writing.
        - Skips any empty files; robust against partial failures (e.g., missing HTML).
    """
    # Compute entry mtimes ourselves from current UTC time. We deliberately
    # bypass CPython's default ZipInfo construction path
    # (ZipInfo._for_archive), because it honors `SOURCE_DATE_EPOCH` via
    # time.localtime() – which produces invalid pre-1980 DOS dates in any
    # timezone west of UTC. That path crashes with: `struct.error: 'H' format
    # requires 0 <= number <= 65535`.
    #
    # Using gmtime() makes the timestamp timezone-agnostic and ensures DOS-date
    # math (year - 1980) is always non-negative for any sane "now".
    now_utc = time.gmtime()
    entry_date_time = (
        now_utc.tm_year,
        now_utc.tm_mon,
        now_utc.tm_mday,
        now_utc.tm_hour,
        now_utc.tm_min,
        now_utc.tm_sec,
    )

    zip_buffer = io.BytesIO()

    with ZipFile(zip_buffer, "w") as zf:
        for item in zip_package.get_items():
            content = item.file_content
            filename = item.file_name

            if not content:
                continue
            data = content if isinstance(content, bytes) else content.encode("utf-8")
            zinfo = ZipInfo(filename=filename, date_time=entry_date_time)
            zinfo.compress_type = zf.compression
            zf.writestr(zinfo, data)

    zip_buffer.seek(0)
    return zip_package.get_name(), zip_buffer


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

    from app.api.validation.file_validation import UNCOMPRESSED_MAX_BYTES

    file_size_sum = sum(zinfo.file_size for zinfo in info)
    return file_size_sum < UNCOMPRESSED_MAX_BYTES


async def read_xml_zip(file: FileUpload) -> XMLFiles:
    """
    Read XML files from a ZIP archive.
    """
    from app.api.validation.file_validation import UNCOMPRESSED_MAX_MB

    try:
        file_content = await file.read()
        with ZipFile(BytesIO(file_content), "r") as zf:
            eicr_xml = None
            rr_xml = None

            if not _is_valid_uncompressed_size(zf.infolist()):
                raise ZipSizeError(
                    message=f"Uncompressed .zip file must not exceed {UNCOMPRESSED_MAX_MB}MB in size."
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
                    message="Required file CDA_eICR.xml not found in .zip file or was empty.",
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
                    message="Required file CDA_RR.xml not found in .zip file or was empty",
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
    except ZipSizeError:
        # re-raise ZipSizeError without wrapping it
        raise
    except Exception as e:
        raise FileProcessingError(
            message="Failed to process ZIP file", details={"error": str(e)}
        )

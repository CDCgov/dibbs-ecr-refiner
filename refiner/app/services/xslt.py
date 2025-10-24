"""
XSLT Transformation Utility for CDA XML -> HTML.

This module provides a secure, robust function for transforming CDA XML documents to HTML using a vetted XSLT stylesheet.
"""

from io import BytesIO
from logging import Logger
from pathlib import Path

from lxml import etree

from ..services.file_io import get_asset_path


def get_path_to_xslt_stylesheet() -> Path:
    """Returns the path to the eICR XSLT stylesheet."""

    return get_asset_path("xslt", "CDA-phcaserpt-1.1.1-CDAR2_eCR_eICR.xsl")


class XSLTTransformationError(Exception):
    """Custom exception for XSLT transformation errors."""

    pass


def transform_xml_to_html(xml_bytes: bytes, xslt_path: Path, logger: Logger) -> bytes:
    """
    Transforms CDA XML to HTML using the specified XSLT stylesheet.

    Args:
        xml_bytes (bytes): The raw XML document bytes.
        xslt_path (Path): Path to the XSLT stylesheet file.
        logger (Logger): Logger for logging errors and debug information.

    Returns:
        bytes: The resulting HTML bytes.

    Raises:
        XSLTTransformationError: If transformation fails for any reason.
    """
    try:
        # Secure parser settings: no DTD, no external entities
        parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            dtd_validation=False,
            load_dtd=False,
        )
        xml_doc = etree.parse(BytesIO(xml_bytes), parser)
        logger.debug("Parsed XML input successfully.")
    except (etree.XMLSyntaxError, Exception) as e:
        logger.error(f"Failed to parse XML input: {e}")
        raise XSLTTransformationError("Malformed XML input.") from e
    try:
        # Ensure xslt_path is within the trusted xslt asset directory to
        # prevent directory traversal
        base_xslt_dir = get_asset_path("xslt")
        resolved_xslt_path = xslt_path.resolve()
        base_xslt_dir_resolved = base_xslt_dir.resolve()
        try:
            # This will throw ValueError if resolved_xslt_path is not inside base_xslt_dir_resolved
            resolved_xslt_path.relative_to(base_xslt_dir_resolved)
        except ValueError:
            logger.error(
                f"Attempted access to stylesheet outside trusted directory: {resolved_xslt_path}"
            )
            raise XSLTTransformationError(
                "Access to XSLT file outside trusted directory is not allowed."
            )
        with open(resolved_xslt_path, "rb") as xslt_file:
            xslt_doc = etree.parse(xslt_file, parser)
        xslt_transform = etree.XSLT(xslt_doc)
        logger.debug(f"Loaded XSLT stylesheet from {resolved_xslt_path}.")
    except XSLTTransformationError:
        raise
    except (FileNotFoundError, etree.XMLSyntaxError, Exception) as e:
        logger.error(f"Failed to load/parse XSLT file: {e}")
        raise XSLTTransformationError("Malformed or missing XSLT file.") from e
    try:
        result = xslt_transform(xml_doc)
        html_bytes = etree.tostring(result, encoding="utf-8")
        logger.debug("XSLT transformation succeeded.")
        return html_bytes
    except (etree.XSLTApplyError, Exception) as e:
        logger.error(f"XSLT transformation failed: {e}")
        raise XSLTTransformationError("XSLT transformation failed.") from e

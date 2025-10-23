"""
XSLT Transformation Utility for CDA XML -> HTML.

This module provides a secure, robust function for transforming CDA XML documents to HTML using a vetted XSLT stylesheet.
"""

from io import BytesIO
from logging import Logger

from lxml import etree


class XSLTTransformationError(Exception):
    """Custom exception for XSLT transformation errors."""

    pass


def transform_xml_to_html(xml_bytes: bytes, xslt_path: str, logger: Logger) -> bytes:
    """
    Transforms CDA XML to HTML using the specified XSLT stylesheet.

    Args:
        xml_bytes (bytes): The raw XML document bytes.
        xslt_path (str): Path to the XSLT stylesheet file.
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
        with open(xslt_path, "rb") as xslt_file:
            xslt_doc = etree.parse(xslt_file, parser)
        xslt_transform = etree.XSLT(xslt_doc)
        logger.debug(f"Loaded XSLT stylesheet from {xslt_path}.")
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

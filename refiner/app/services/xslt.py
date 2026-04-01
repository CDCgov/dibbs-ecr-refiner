"""
XSLT Transformation Utility for CDA XML -> HTML.

This module provides a secure, robust function for transforming CDA XML documents to HTML using a vetted XSLT stylesheet.
"""

from io import BytesIO
from logging import Logger
from pathlib import Path

from lxml import etree

from app.services.assets import get_asset_path
from app.services.ecr.model import ReportableCondition
from app.services.file_io import ZipFileItem


def _get_path_to_xslt_stylesheet() -> Path:
    """Returns the path to the eICR XSLT stylesheet."""

    return get_asset_path("xslt", "CDA-phcaserpt-1.1.1-CDAR2_eCR_eICR.xsl")


class XSLTTransformationError(Exception):
    """Custom exception for XSLT transformation errors."""

    pass


def _transform_xml_to_html(xml_bytes: bytes, xslt_path: Path, logger: Logger) -> bytes:
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


def create_refined_eicr_html_file(
    condition: ReportableCondition, refined_eicr: str, file_name: str, logger: Logger
) -> ZipFileItem:
    """
    Creates an HTML file using the refined condition's eICR information.

    Args:
        condition (ReportableCondition): The reportable condition
        refined_eicr (str): Condition's refined eICR document
        file_name (str): Desired HTML file name
        logger (Logger): The logger

    Returns:
        ZippedItem: A processed object ready for packing into a zip file.
    """
    try:
        xslt_stylesheet_path = _get_path_to_xslt_stylesheet()
        html_bytes = _transform_xml_to_html(
            refined_eicr.encode("utf-8"), xslt_stylesheet_path, logger
        )

        logger.info(
            f"Successfully transformed XML to HTML for condition: {condition.display_name}",
            extra={
                "condition_code": condition.code,
                "condition_name": condition.display_name,
            },
        )
        return ZipFileItem(file_name=file_name, file_content=html_bytes.decode("utf-8"))
    except XSLTTransformationError as e:
        logger.error(
            f"Failed to transform XML to HTML for condition: {condition.display_name}",
            extra={
                "condition_code": condition.code,
                "condition_name": condition.display_name,
                "error": str(e),
            },
        )
        raise

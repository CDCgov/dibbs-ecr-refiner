import logging
import os
import tempfile
from pathlib import Path

import pytest

from app.services.xslt import XSLTTransformationError, transform_xml_to_html

BAD_CDA_XML = b"<ClinicalDocument><bad><xml></ClinicalDocument>"  # Malformed XML
MINIMAL_XSLT = b"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" />
  <xsl:template match="/ClinicalDocument">
    <html><body><h1>OK</h1></body></html>
  </xsl:template>
</xsl:stylesheet>"""
BAD_XSLT = b'<xsl:stylesheet version="1.0"><xsl:output/></bad></xsl:stylesheet>'  # Malformed XSLT


def test_transform_xml_to_html_malformed_xml() -> None:
    """
    Should raise XSLTTransformationError on malformed XML.
    """
    with tempfile.NamedTemporaryFile(suffix=".xslt") as xslt_file:
        xslt_file.write(MINIMAL_XSLT)
        xslt_file.flush()
        with pytest.raises(XSLTTransformationError):
            transform_xml_to_html(
                BAD_CDA_XML, xslt_file.name, logging.getLogger("xslt-test")
            )


def test_transform_xml_to_html_malformed_xslt() -> None:
    """
    Should raise XSLTTransformationError on malformed XSLT.
    """
    VALID_CDA_XML = b"""
    <ClinicalDocument xmlns="urn:hl7-org:v3">
      <recordTarget></recordTarget>
    </ClinicalDocument>
    """
    with tempfile.NamedTemporaryFile(suffix=".xslt") as xslt_file:
        xslt_file.write(BAD_XSLT)
        xslt_file.flush()
        with pytest.raises(XSLTTransformationError):
            transform_xml_to_html(
                VALID_CDA_XML, xslt_file.name, logging.getLogger("xslt-test")
            )


def test_transform_xml_to_html_xslt_outside_trusted_directory() -> None:
    """
    Should raise XSLTTransformationError if xslt file is outside trusted directory.
    """
    VALID_CDA_XML = b"""
    <ClinicalDocument xmlns="urn:hl7-org:v3">
      <recordTarget></recordTarget>
    </ClinicalDocument>
    """
    with tempfile.NamedTemporaryFile(
        suffix=".xslt", dir=tempfile.gettempdir(), delete=False
    ) as xslt_file:
        xslt_file.write(MINIMAL_XSLT)
        xslt_file.flush()
        xslt_file_path = Path(xslt_file.name)
    try:
        # This file is definitely not under the assets/xslt trusted dir.
        with pytest.raises(XSLTTransformationError) as exc_info:
            transform_xml_to_html(
                VALID_CDA_XML, xslt_file_path, logging.getLogger("xslt-test")
            )
        assert "outside trusted directory" in str(exc_info.value)
    finally:
        os.unlink(xslt_file_path)

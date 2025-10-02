from lxml import etree

from app.core.exceptions import XMLParsingError
from app.core.models.types import XMLFiles
from app.services.ecr.models import ProcessedRR

from .process_rr import get_reportable_conditions_by_jurisdiction


def determine_reportability(xml_files: XMLFiles) -> ProcessedRR:
    """
    Process the RR XML document to extract reportable condition data.

    Args:
        xml_files: Container with both eICR and RR XML content
                  (currently only using RR)

    Returns:
        ProcessedRR: Mapping of jurisdiction code to list of reportable conditions

    Raises:
        XMLParsingError
    """

    try:
        rr_root = xml_files.parse_rr()
        return {
            "reportable_conditions": get_reportable_conditions_by_jurisdiction(rr_root)
        }
    except etree.XMLSyntaxError as e:
        raise XMLParsingError(
            message="Failed to parse RR document", details={"error": str(e)}
        )

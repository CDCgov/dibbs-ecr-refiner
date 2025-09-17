import pytest
from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import StructureValidationError, XMLValidationError
from app.core.models.types import XMLFiles
from app.services.ecr.models import ReportableCondition
from app.services.ecr.process_rr import _get_reportable_conditions, process_rr

# NOTE:
# PUBLIC API FUNCTION TESTS


def test_process_rr_with_valid_xml():
    rr_xml = """
    <ClinicalDocument xmlns="urn:hl7-org:v3">
      <component>
        <section>
          <code code="55112-7"/>
          <entry>
            <organizer>
              <code code="RR11"/>
              <component>
                <observation>
                  <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                  <value codeSystem="2.16.840.1.113883.6.96"
                         code="840539006"
                         displayName="COVID-19"/>
                  <entryRelationship>
                    <observation>
                      <code code="RR1"/>
                      <value code="RRVS1"/>
                    </observation>
                  </entryRelationship>
                </observation>
              </component>
            </organizer>
          </entry>
        </section>
      </component>
    </ClinicalDocument>
    """
    xml_files = XMLFiles(eicr=None, rr=rr_xml)
    result = process_rr(xml_files)
    # Should extract one reportable condition
    assert "reportable_conditions" in result
    assert result["reportable_conditions"] == [
        ReportableCondition(code="840539006", display_name="COVID-19")
    ]


def test_process_rr_with_invalid_xml():
    invalid_rr_xml = "<ClinicalDocument><notclosed></ClinicalDocument"
    xml_files = XMLFiles(eicr=None, rr=invalid_rr_xml)
    with pytest.raises(XMLValidationError):
        process_rr(xml_files)


def test_process_rr_with_no_reportable_conditions():
    rr_xml = """
    <ClinicalDocument xmlns="urn:hl7-org:v3">
      <component>
        <section>
          <code code="55112-7"/>
          <entry>
            <organizer>
              <code code="RR11"/>
            </organizer>
          </entry>
        </section>
      </component>
    </ClinicalDocument>
    """
    xml_files = XMLFiles(eicr=None, rr=rr_xml)
    result = process_rr(xml_files)
    assert "reportable_conditions" in result
    assert result["reportable_conditions"] == []


# NOTE:
# PRIVATE API FUNCTION TESTS


def test_get_reportable_conditions_no_codes() -> None:
    """
    Test _get_reportable_conditions when no codes are found.
    """

    root: _Element = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                </section>
            </component>
        </ClinicalDocument>
    """)

    with pytest.raises(StructureValidationError) as exc_info:
        _get_reportable_conditions(root)

    assert "Missing required RR11 Coded Information Organizer" in str(exc_info.value)


def test_get_reportable_conditions_uniqueness() -> None:
    """
    Test that get_reportable_conditions returns unique conditions only.
    Uses sample RR with duplicate reportable conditions to verify deduplication.
    """

    root: _Element = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                    <entry>
                        <organizer>
                            <code code="RR11"/>
                            <!-- First occurrence of condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="840539006"
                                          displayName="COVID-19"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                            <!-- Duplicate condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="840539006"
                                          displayName="COVID-19"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                            <!-- Different condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                          code="27836007"
                                          displayName="Pertussis"/>
                                    <entryRelationship>
                                        <observation>
                                            <code code="RR1"/>
                                            <value code="RRVS1"/>
                                        </observation>
                                    </entryRelationship>
                                </observation>
                            </component>
                        </organizer>
                    </entry>
                </section>
            </component>
        </ClinicalDocument>
    """)

    result = _get_reportable_conditions(root)

    # verify we get exactly 2 unique conditions
    assert len(result) == 2

    # verify the specific conditions are present
    expected_conditions: list[ReportableCondition] = [
        ReportableCondition(code="840539006", display_name="COVID-19"),
        ReportableCondition(code="27836007", display_name="Pertussis"),
    ]
    assert result == expected_conditions


def test_get_reportable_conditions_empty_rr11() -> None:
    """
    Test that RR11 organizer with no qualifying observations returns None.
    """

    root: _Element = etree.fromstring("""
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <component>
                <section>
                    <code code="55112-7"/>
                    <entry>
                        <organizer>
                            <code code="RR11"/>
                            <!-- Empty RR11 organizer -->
                        </organizer>
                    </entry>
                </section>
            </component>
        </ClinicalDocument>
    """)

    result = _get_reportable_conditions(root)
    assert result == []

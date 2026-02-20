import pytest

from app.core.exceptions import XMLValidationError
from app.core.models.types import XMLFiles
from app.services.ecr.models import ReportableCondition
from app.services.ecr.reportability import determine_reportability


def test_determine_reportability_with_valid_xml():
    """
    Test determine_reportability with a simplified version of our test RR data.
    """

    rr_xml = """
    <ClinicalDocument xmlns="urn:hl7-org:v3"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                    <organizer>
                      <!-- Routing Entity: SDDH -->
                      <participant>
                        <participantRole>
                          <id extension="SDDH" root="2.16.840.1.113883.4.6"/>
                          <code code="RR7"
                                codeSystem="2.16.840.1.114222.4.5.232"
                                codeSystemName="PHIN Questions"
                                displayName="Routing Entity"/>
                        </participantRole>
                      </participant>
                      <!-- Reportability determination -->
                      <component>
                        <observation>
                          <code code="RR1"/>
                          <value code="RRVS1"/>
                        </observation>
                      </component>
                    </organizer>
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
    result = determine_reportability(xml_files)

    # check that reportable_conditions is present and is a non-empty list
    assert "reportable_conditions" in result
    assert isinstance(result["reportable_conditions"], list)
    assert len(result["reportable_conditions"]) == 1

    jurisdiction_group = result["reportable_conditions"][0]
    assert jurisdiction_group.jurisdiction == "SDDH"
    assert jurisdiction_group.conditions == [
        ReportableCondition(code="840539006", display_name="COVID-19")
    ]


def test_determine_reportability_with_malformed_case_jd_code():
    """
    Test determine_reportability with a simplified version of our test RR data, checking the case where the JD ID isn't fully upper cased.
    """

    rr_xml = """
    <ClinicalDocument xmlns="urn:hl7-org:v3"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                    <organizer>
                      <!-- Routing Entity: SDDH -->
                      <participant>
                        <participantRole>
                          <id extension="sdDh" root="2.16.840.1.113883.4.6"/>
                          <code code="RR7"
                                codeSystem="2.16.840.1.114222.4.5.232"
                                codeSystemName="PHIN Questions"
                                displayName="Routing Entity"/>
                        </participantRole>
                      </participant>
                      <!-- Reportability determination -->
                      <component>
                        <observation>
                          <code code="RR1"/>
                          <value code="RRVS1"/>
                        </observation>
                      </component>
                    </organizer>
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
    result = determine_reportability(xml_files)

    # check that reportable_conditions is present and is a non-empty list
    assert "reportable_conditions" in result
    assert isinstance(result["reportable_conditions"], list)
    assert len(result["reportable_conditions"]) == 1

    jurisdiction_group = result["reportable_conditions"][0]
    assert jurisdiction_group.jurisdiction == "SDDH"
    assert jurisdiction_group.conditions == [
        ReportableCondition(code="840539006", display_name="COVID-19")
    ]


def test_determine_reportability_with_invalid_xml():
    invalid_rr_xml = "<ClinicalDocument><notclosed></ClinicalDocument"
    xml_files = XMLFiles(eicr=None, rr=invalid_rr_xml)
    with pytest.raises(XMLValidationError):
        determine_reportability(xml_files)


def test_determine_reportability_with_no_reportable_conditions():
    """
    Test that determine_reportability returns no reportable conditions if there are none.

    Covers the case where RR11 exists, but no RR7/routing entities or reportable observations.
    """

    rr_xml = """
    <ClinicalDocument xmlns="urn:hl7-org:v3">
      <component>
        <section>
          <code code="55112-7"/>
          <entry>
            <organizer>
              <code code="RR11"/>
              <!-- Non-reportable condition (no RR1/RRVS1, no RR7) -->
              <component>
                <observation>
                  <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                  <value codeSystem="2.16.840.1.113883.6.96"
                         code="840539006"
                         displayName="COVID-19"/>
                  <!-- No entryRelationship/organizer/RR7 -->
                </observation>
              </component>
            </organizer>
          </entry>
        </section>
      </component>
    </ClinicalDocument>
    """

    xml_files = XMLFiles(eicr=None, rr=rr_xml)
    result = determine_reportability(xml_files)
    assert "reportable_conditions" in result
    assert result["reportable_conditions"] == []

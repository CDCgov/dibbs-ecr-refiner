import pytest
from lxml import etree
from lxml.etree import _Element

from app.core.exceptions import StructureValidationError
from app.services.ecr.models import ReportableCondition
from app.services.ecr.process_rr import get_reportable_conditions_by_jurisdiction


def test_get_reportable_conditions_no_codes() -> None:
    """
    Test _get_reportable_conditions_by_jurisdiction when no codes are found.
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
        get_reportable_conditions_by_jurisdiction(root)

    assert "Missing required RR11 Coded Information Organizer" in str(exc_info.value)


def test_get_reportable_conditions_uniqueness() -> None:
    """
    Test that get_reportable_conditions_by_jurisdiction returns unique conditions per jurisdiction.

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
                            <!-- All conditions are under the same jurisdiction for simplicity -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                           code="840539006"
                                           displayName="COVID-19"/>
                                    <entryRelationship>
                                        <organizer>
                                            <participant>
                                                <participantRole>
                                                    <id extension="JUR1" root="2.16.840.1.113883.4.6"/>
                                                    <code code="RR7" />
                                                </participantRole>
                                            </participant>
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
                            <!-- Duplicate condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                           code="840539006"
                                           displayName="COVID-19"/>
                                    <entryRelationship>
                                        <organizer>
                                            <participant>
                                                <participantRole>
                                                    <id extension="JUR1" root="2.16.840.1.113883.4.6"/>
                                                    <code code="RR7" />
                                                </participantRole>
                                            </participant>
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
                            <!-- Different condition -->
                            <component>
                                <observation>
                                    <templateId root="2.16.840.1.113883.10.20.15.2.3.12"/>
                                    <value codeSystem="2.16.840.1.113883.6.96"
                                           code="27836007"
                                           displayName="Pertussis"/>
                                    <entryRelationship>
                                        <organizer>
                                            <participant>
                                                <participantRole>
                                                    <id extension="JUR1" root="2.16.840.1.113883.4.6"/>
                                                    <code code="RR7" />
                                                </participantRole>
                                            </participant>
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
    """)

    result = get_reportable_conditions_by_jurisdiction(root)

    # should be one jurisdiction group: "JUR1"
    assert len(result) == 1
    jurisdiction_group = result[0]
    assert jurisdiction_group.jurisdiction == "JUR1"

    # should deduplicate conditions, so only two unique conditions returned
    expected_conditions: list[ReportableCondition] = [
        ReportableCondition(code="840539006", display_name="COVID-19"),
        ReportableCondition(code="27836007", display_name="Pertussis"),
    ]
    assert sorted(jurisdiction_group.conditions, key=lambda c: c.code) == sorted(
        expected_conditions, key=lambda c: c.code
    )


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

    result = get_reportable_conditions_by_jurisdiction(root)
    assert result == []

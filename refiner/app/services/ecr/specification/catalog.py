from typing import Final

from ..model import SectionSpecification
from .entry_match_rules import (
    _ADMISSION_DIAGNOSIS_MATCH_RULES,
    _ADMISSION_MEDICATIONS_MATCH_RULES,
    _DISCHARGE_DIAGNOSIS_MATCH_RULES,
    _ENCOUNTERS_MATCH_RULES,
    _IMMUNIZATIONS_MATCH_RULES,
    _MEDICATIONS_HOME_MATCH_RULES,
    _MEDICATIONS_MATCH_RULES,
    _PAST_MEDICAL_HISTORY_MATCH_RULES,
    _PLAN_OF_TREATMENT_MATCH_RULES,
    _PROBLEM_MATCH_RULES,
    _RESULTS_MATCH_RULES,
    _VITAL_SIGNS_MATCH_RULES,
)

# NOTE:
# SECTION CATALOG
# =============================================================================

_SECTION_CATALOG: Final[dict[str, SectionSpecification]] = {
    # sections present in all versions (1.1, 3.1, 3.1.1)
    "46240-8": SectionSpecification(
        loinc_code="46240-8",
        display_name="Encounters Section",
        template_id="2.16.840.1.113883.10.20.22.2.22.1:2015-08-01",
        entry_match_rules=_ENCOUNTERS_MATCH_RULES,
    ),
    "10164-2": SectionSpecification(
        loinc_code="10164-2",
        display_name="History of Present Illness Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.3.4",
    ),
    "11369-6": SectionSpecification(
        loinc_code="11369-6",
        display_name="Immunizations Section",
        template_id="2.16.840.1.113883.10.20.22.2.2.1:2015-08-01",
        entry_match_rules=_IMMUNIZATIONS_MATCH_RULES,
    ),
    "29549-3": SectionSpecification(
        loinc_code="29549-3",
        display_name="Medications Administered Section",
        template_id="2.16.840.1.113883.10.20.22.2.38:2014-06-09",
        entry_match_rules=_MEDICATIONS_MATCH_RULES,
    ),
    "18776-5": SectionSpecification(
        loinc_code="18776-5",
        display_name="Plan of Treatment Section",
        template_id="2.16.840.1.113883.10.20.22.2.10:2014-06-09",
        entry_match_rules=_PLAN_OF_TREATMENT_MATCH_RULES,
    ),
    "11450-4": SectionSpecification(
        loinc_code="11450-4",
        display_name="Problem Section",
        template_id="2.16.840.1.113883.10.20.22.2.5.1:2015-08-01",
        entry_match_rules=_PROBLEM_MATCH_RULES,
    ),
    "29299-5": SectionSpecification(
        loinc_code="29299-5",
        display_name="Reason for Visit Section",
        template_id="2.16.840.1.113883.10.20.22.2.12",
    ),
    "30954-2": SectionSpecification(
        loinc_code="30954-2",
        display_name="Results Section",
        template_id="2.16.840.1.113883.10.20.22.2.3.1:2015-08-01",
        entry_match_rules=_RESULTS_MATCH_RULES,
    ),
    "29762-2": SectionSpecification(
        loinc_code="29762-2",
        display_name="Social History Section",
        template_id="2.16.840.1.113883.10.20.22.2.17:2015-08-01",
    ),
    # sections added in 3.1+
    "10187-3": SectionSpecification(
        loinc_code="10187-3",
        display_name="Review of Systems Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.3.18",
    ),
    "10154-3": SectionSpecification(
        loinc_code="10154-3",
        display_name="Chief Complaint Section",
        template_id="1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1",
    ),
    "10160-0": SectionSpecification(
        loinc_code="10160-0",
        display_name="Medications Section",
        template_id="2.16.840.1.113883.10.20.22.2.1.1:2014-06-09",
        entry_match_rules=_MEDICATIONS_HOME_MATCH_RULES,
    ),
    "47519-4": SectionSpecification(
        loinc_code="47519-4",
        display_name="Procedures Section",
        template_id="2.16.840.1.113883.10.20.22.2.7.1:2014-06-09",
    ),
    "46241-6": SectionSpecification(
        loinc_code="46241-6",
        display_name="Admission Diagnosis Section",
        template_id="2.16.840.1.113883.10.20.22.2.43:2015-08-01",
        entry_match_rules=_ADMISSION_DIAGNOSIS_MATCH_RULES,
    ),
    "11535-2": SectionSpecification(
        loinc_code="11535-2",
        display_name="Discharge Diagnosis Section",
        template_id="2.16.840.1.113883.10.20.22.2.24:2015-08-01",
        entry_match_rules=_DISCHARGE_DIAGNOSIS_MATCH_RULES,
    ),
    "42346-7": SectionSpecification(
        loinc_code="42346-7",
        display_name="Admission Medications Section",
        template_id="2.16.840.1.113883.10.20.22.2.44:2015-08-01",
        entry_match_rules=_ADMISSION_MEDICATIONS_MATCH_RULES,
    ),
    "11348-0": SectionSpecification(
        loinc_code="11348-0",
        display_name="Past Medical History Section",
        template_id="2.16.840.1.113883.10.20.22.2.20:2015-08-01",
        entry_match_rules=_PAST_MEDICAL_HISTORY_MATCH_RULES,
    ),
    "8716-3": SectionSpecification(
        loinc_code="8716-3",
        display_name="Vital Signs Section",
        template_id="2.16.840.1.113883.10.20.22.2.4.1:2015-08-01",
        entry_match_rules=_VITAL_SIGNS_MATCH_RULES,
    ),
    "90767-5": SectionSpecification(
        loinc_code="90767-5",
        display_name="Pregnancy Section",
        template_id="2.16.840.1.113883.10.20.22.2.80:2018-04-01",
    ),
    "83910-0": SectionSpecification(
        loinc_code="83910-0",
        display_name="Emergency Outbreak Information Section",
        template_id="2.16.840.1.113883.10.20.15.2.2.4:2021-01-01",
    ),
    "88085-6": SectionSpecification(
        loinc_code="88085-6",
        display_name="Reportability Response Information Section",
        template_id="2.16.840.1.113883.10.20.15.2.2.5:2021-01-01",
    ),
}

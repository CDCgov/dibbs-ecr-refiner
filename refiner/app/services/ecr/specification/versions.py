from typing import Final

from ..model import EicrVersion, TriggerCode

# NOTE:
# TYPE ALIAS
# =============================================================================
# format: dict of section LOINC -> list of TriggerCode instances applicable
# to that section in a given version

type TriggerMap = dict[str, list[TriggerCode]]


# NOTE:
# VERSION 1.1 TRIGGER MANIFEST
# =============================================================================

_VERSION_1_1_TRIGGERS: Final[TriggerMap] = {
    "46240-8": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.5:2016-12-01",
            display_name="Initial Case Report Manual Initiation Reason Observation",
            element_tag="observation",
        ),
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.3:2016-12-01",
            display_name="Initial Case Report Trigger Code Problem Observation",
            element_tag="observation",
        ),
    ],
    "18776-5": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.4:2016-12-01",
            display_name="Initial Case Report Trigger Code Lab Test Order",
            element_tag="observation",
        ),
    ],
    "30954-2": [
        TriggerCode(
            oid="2.16.840.1.113883.10.20.15.2.3.2:2016-12-01",
            display_name="Initial Case Report Trigger Code Result Observation",
            element_tag="observation",
        ),
    ],
}


# NOTE:
# VERSION 3.x SHARED TRIGGER CONSTANTS
# =============================================================================
# reusable TriggerCode instances referenced by _VERSION_3X_TRIGGERS below.
# defined as module-level constants so each trigger template appears once
# even when it's used by multiple sections

_trigger_code_problem_obs_v3 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.3:2021-01-01",
    display_name="Initial Case Report Trigger Code Problem Observation",
    element_tag="observation",
)
_trigger_code_med_info = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.36:2019-04-01",
    display_name="Initial Case Report Trigger Code Medication Information",
    element_tag="manufacturedProduct",
)
_trigger_code_immunization_info = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.38:2019-04-01",
    display_name="Initial Case Report Trigger Code Immunization Medication Information",
    element_tag="manufacturedProduct",
)
_trigger_code_result_obs_v2 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.2:2019-04-01",
    display_name="Initial Case Report Trigger Code Result Observation",
    element_tag="observation",
)
_trigger_code_result_organizer = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.35:2022-05-01",
    display_name="Initial Case Report Trigger Code Result Organizer",
    element_tag="organizer",
)
_trigger_code_lab_test_order_v2 = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.4:2019-04-01",
    display_name="Initial Case Report Trigger Code Lab Test Order",
    element_tag="observation",
)
_trigger_code_planned_act = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.41:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Act",
    element_tag="act",
)
_trigger_code_planned_procedure = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.42:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Procedure",
    element_tag="procedure",
)
_trigger_code_planned_observation = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.43:2021-01-01",
    display_name="Initial Case Report Trigger Code Planned Observation",
    element_tag="observation",
)
_trigger_code_procedure_act = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.45:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Act",
    element_tag="act",
)
_trigger_code_procedure_obs = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.46:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Observation",
    element_tag="observation",
)
_trigger_code_procedure_procedure = TriggerCode(
    oid="2.16.840.1.113883.10.20.15.2.3.44:2021-01-01",
    display_name="Initial Case Report Trigger Code Procedure Activity Procedure",
    element_tag="procedure",
)


# NOTE:
# VERSION 3.x TRIGGER MANIFEST (SHARED BY 3.1 AND 3.1.1)
# =============================================================================

_VERSION_3X_TRIGGERS: Final[TriggerMap] = {
    "10160-0": [_trigger_code_med_info],
    "18776-5": [
        _trigger_code_lab_test_order_v2,
        _trigger_code_planned_act,
        _trigger_code_planned_procedure,
        _trigger_code_planned_observation,
        _trigger_code_med_info,
    ],
    "29549-3": [_trigger_code_med_info],
    "47519-4": [
        _trigger_code_med_info,
        _trigger_code_procedure_act,
        _trigger_code_procedure_obs,
        _trigger_code_procedure_procedure,
    ],
    "11369-6": [_trigger_code_immunization_info, _trigger_code_med_info],
    "30954-2": [_trigger_code_result_organizer, _trigger_code_result_obs_v2],
    "42346-7": [_trigger_code_med_info],
    "11450-4": [_trigger_code_problem_obs_v3],
    "46240-8": [_trigger_code_problem_obs_v3],
}


# NOTE:
# SECTIONS PRESENT BY VERSION
# =============================================================================
# which sections exist in each version (by LOINC code). used by the loader
# to assemble the full EICRSpecification for a given version — only sections
# in the relevant list are pulled from the catalog

_VERSION_SECTIONS: Final[dict[EicrVersion, list[str]]] = {
    "1.1": [
        "46240-8",  # Encounters
        "10164-2",  # History of Present Illness
        "11369-6",  # Immunizations
        "29549-3",  # Medications Administered
        "18776-5",  # Plan of Treatment
        "11450-4",  # Problem
        "29299-5",  # Reason for Visit
        "30954-2",  # Results
        "29762-2",  # Social History
    ],
    # 3.1 and 3.1.1 have identical section sets and trigger codes
    "3.1": [
        # all 1.1 sections
        "46240-8",
        "10164-2",
        "11369-6",
        "29549-3",
        "18776-5",
        "11450-4",
        "29299-5",
        "30954-2",
        "29762-2",
        # added in 3.1+
        "10187-3",  # Review of Systems
        "10154-3",  # Chief Complaint
        "10160-0",  # Medications (home)
        "47519-4",  # Procedures
        "46241-6",  # Admission Diagnosis
        "11535-2",  # Discharge Diagnosis
        "42346-7",  # Admission Medications
        "11348-0",  # Past Medical History
        "8716-3",  # Vital Signs
        "90767-5",  # Pregnancy
        "83910-0",  # Emergency Outbreak Information
        "88085-6",  # Reportability Response Information
    ],
}
# 3.1.1 is parsed identically to 3.1
_VERSION_SECTIONS["3.1.1"] = _VERSION_SECTIONS["3.1"]


# NOTE:
# VERSION → TRIGGER MAP
# =============================================================================
# top-level lookup used by the loader: given an EicrVersion, return the
# TriggerMap that overlays trigger codes onto the catalog's section
# specifications

_VERSION_TRIGGERS: Final[dict[EicrVersion, TriggerMap]] = {
    "1.1": _VERSION_1_1_TRIGGERS,
    "3.1": _VERSION_3X_TRIGGERS,
    "3.1.1": _VERSION_3X_TRIGGERS,
}

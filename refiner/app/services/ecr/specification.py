from typing import Final, TypedDict

from lxml.etree import _Element

from .models import (
    EICRSpecification,
    EicrVersion,
    NamespaceMap,
    SectionSpecification,
    TriggerCode,
)

# NOTE:
# TYPE DEFINITIONS FOR RAW DATA
# =============================================================================


class RawTriggerData(TypedDict):
    """
    Shape of a trigger definition in the raw data dictionary.
    """

    element: str
    display: str


class RawSectionData(TypedDict):
    """
    Shape of a section definition in the raw data dictionary.
    """

    display: str
    oid: str
    trigger_codes: dict[str, RawTriggerData]


# map of version -> map of loinc -> section data
type EicrSpecsData = dict[EicrVersion, dict[str, RawSectionData]]


# NOTE:
# CONSTANTS
# =============================================================================

# map of templateId extensions to their semantic version strings
EICR_VERSION_MAP: Final[dict[str, EicrVersion]] = {
    "2016-12-01": "1.1",
    "2021-01-01": "3.1",
    "2022-05-01": "3.1.1",
}

NAMESPACES: Final[NamespaceMap] = {
    "hl7": "urn:hl7-org:v3",
    "cda": "urn:hl7-org:v3",
}

# for CDA sections that we should not refine; in the future we may
# decide to implement new ways to handle these sections but for now;
# skipping them is easier and produces valid (based on schematron) output
SECTION_PROCESSING_SKIP: Final[set[str]] = {
    "83910-0",  # emergency outbreak information section
    "88085-6",  # reportability response information section
}

# the static source of truth for eICR specifications
EICR_SPECS_DATA: Final[EicrSpecsData] = {
    "1.1": {
        "46240-8": {
            "display": "Encounters Section",
            "oid": "2.16.840.1.113883.10.20.22.2.22.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.5:2016-12-01": {
                    "element": "observation",
                    "display": "Initial Case Report Manual Initiation Reason Observation",
                },
                "2.16.840.1.113883.10.20.15.2.3.3:2016-12-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Problem Observation",
                },
            },
        },
        "10164-2": {
            "display": "History of Present Illness Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.3.4",
            "trigger_codes": {},
        },
        "11369-6": {
            "display": "Immunizations Section",
            "oid": "2.16.840.1.113883.10.20.22.2.2.1:2015-08-01",
            "trigger_codes": {},
        },
        "29549-3": {
            "display": "Medications Administered Section",
            "oid": "2.16.840.1.113883.10.20.22.2.38:2014-06-09",
            "trigger_codes": {},
        },
        "18776-5": {
            "display": "Plan of Treatment Section",
            "oid": "2.16.840.1.113883.10.20.22.2.10:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.4:2016-12-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Lab Test Order",
                }
            },
        },
        "11450-4": {
            "display": "Problem Section",
            "oid": "2.16.840.1.113883.10.20.22.2.5.1:2015-08-01",
            "trigger_codes": {},
        },
        "29299-5": {
            "display": "Reason for Visit Section",
            "oid": "2.16.840.1.113883.10.20.22.2.12",
            "trigger_codes": {},
        },
        "30954-2": {
            "display": "Results Section",
            "oid": "2.16.840.1.113883.10.20.22.2.3.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.2:2016-12-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Result Observation",
                }
            },
        },
        "29762-2": {
            "display": "Social History Section",
            "oid": "2.16.840.1.113883.10.20.22.2.17:2015-08-01",
            "trigger_codes": {},
        },
    },
    "3.1": {
        "10187-3": {
            "display": "Review of Systems Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.3.18",
            "trigger_codes": {},
        },
        "10154-3": {
            "display": "Chief Complaint Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1",
            "trigger_codes": {},
        },
        "29299-5": {
            "display": "Reason for Visit Section",
            "oid": "2.16.840.1.113883.10.20.22.2.12",
            "trigger_codes": {},
        },
        "10164-2": {
            "display": "History of Present Illness Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.3.4",
            "trigger_codes": {},
        },
        "10160-0": {
            "display": "Medications Section",
            "oid": "2.16.840.1.113883.10.20.22.2.1.1:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "18776-5": {
            "display": "Plan of Treatment Section",
            "oid": "2.16.840.1.113883.10.20.22.2.10:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.4:2019-04-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Lab Test Order",
                },
                "2.16.840.1.113883.10.20.15.2.3.41:2021-01-01": {
                    "element": "act",
                    "display": "Initial Case Report Trigger Code Planned Act",
                },
                "2.16.840.1.113883.10.20.15.2.3.42:2021-01-01": {
                    "element": "procedure",
                    "display": "Initial Case Report Trigger Code Planned Procedure",
                },
                "2.16.840.1.113883.10.20.15.2.3.43:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Planned Observation",
                },
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
            },
        },
        "29549-3": {
            "display": "Medications Administered Section",
            "oid": "2.16.840.1.113883.10.20.22.2.38:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "47519-4": {
            "display": "Procedures Section",
            "oid": "2.16.840.1.113883.10.20.22.2.7.1:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
                "2.16.840.1.113883.10.20.15.2.3.45:2021-01-01": {
                    "element": "act",
                    "display": "Initial Case Report Trigger Code Procedure Activity Act",
                },
                "2.16.840.1.113883.10.20.15.2.3.46:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Procedure Activity Observation",
                },
                "2.16.840.1.113883.10.20.15.2.3.44:2021-01-01": {
                    "element": "procedure",
                    "display": "Initial Case Report Trigger Code Procedure Activity Procedure",
                },
            },
        },
        "46241-6": {
            "display": "Admission Diagnosis Section",
            "oid": "2.16.840.1.113883.10.20.22.2.43:2015-08-01",
            "trigger_codes": {},
        },
        "11369-6": {
            "display": "Immunizations Section",
            "oid": "2.16.840.1.113883.10.20.22.2.2.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.38:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Immunization Medication Information",
                },
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
            },
        },
        "11535-2": {
            "display": "Discharge Diagnosis Section",
            "oid": "2.16.840.1.113883.10.20.22.2.24:2015-08-01",
            "trigger_codes": {},
        },
        "30954-2": {
            "display": "Results Section",
            "oid": "2.16.840.1.113883.10.20.22.2.3.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.35:2022-05-01": {
                    "element": "organizer",
                    "display": "Initial Case Report Trigger Code Result Organizer",
                },
                "2.16.840.1.113883.10.20.15.2.3.2:2019-04-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Result Observation",
                },
            },
        },
        "42346-7": {
            "display": "Admission Medications Section",
            "oid": "2.16.840.1.113883.10.20.22.2.44:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "11348-0": {
            "display": "Past Medical History",
            "oid": "2.16.840.1.113883.10.20.22.2.20:2015-08-01",
            "trigger_codes": {},
        },
        "8716-3": {
            "display": "Vital Signs Section",
            "oid": "2.16.840.1.113883.10.20.22.2.4.1:2015-08-01",
            "trigger_codes": {},
        },
        "11450-4": {
            "display": "Problem Section",
            "oid": "2.16.840.1.113883.10.20.22.2.5.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.3:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Problem Observation",
                }
            },
        },
        "29762-2": {
            "display": "Social History Section",
            "oid": "2.16.840.1.113883.10.20.22.2.17:2015-08-01",
            "trigger_codes": {},
        },
        "46240-8": {
            "display": "Encounters Section",
            "oid": "2.16.840.1.113883.10.20.22.2.22.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.3:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Problem Observation",
                }
            },
        },
        "90767-5": {
            "display": "Pregnancy Section",
            "oid": "2.16.840.1.113883.10.20.22.2.80:2018-04-01",
            "trigger_codes": {},
        },
        "83910-0": {
            "display": "Emergency Outbreak Information Section",
            "oid": "2.16.840.1.113883.10.20.15.2.2.4:2021-01-01",
            "trigger_codes": {},
        },
        "88085-6": {
            "display": "Reportability Response Information Section",
            "oid": "2.16.840.1.113883.10.20.15.2.2.5:2021-01-01",
            "trigger_codes": {},
        },
    },
    "3.1.1": {
        "10187-3": {
            "display": "Review of Systems Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.3.18",
            "trigger_codes": {},
        },
        "10154-3": {
            "display": "Chief Complaint Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.1.13.2.1",
            "trigger_codes": {},
        },
        "29299-5": {
            "display": "Reason for Visit Section",
            "oid": "2.16.840.1.113883.10.20.22.2.12",
            "trigger_codes": {},
        },
        "10164-2": {
            "display": "History of Present Illness Section",
            "oid": "1.3.6.1.4.1.19376.1.5.3.1.3.4",
            "trigger_codes": {},
        },
        "10160-0": {
            "display": "Medications Section",
            "oid": "2.16.840.1.113883.10.20.22.2.1.1:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "18776-5": {
            "display": "Plan of Treatment Section",
            "oid": "2.16.840.1.113883.10.20.22.2.10:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.4:2019-04-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Lab Test Order",
                },
                "2.16.840.1.113883.10.20.15.2.3.41:2021-01-01": {
                    "element": "act",
                    "display": "Initial Case Report Trigger Code Planned Act",
                },
                "2.16.840.1.113883.10.20.15.2.3.42:2021-01-01": {
                    "element": "procedure",
                    "display": "Initial Case Report Trigger Code Planned Procedure",
                },
                "2.16.840.1.113883.10.20.15.2.3.43:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Planned Observation",
                },
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
            },
        },
        "29549-3": {
            "display": "Medications Administered Section",
            "oid": "2.16.840.1.113883.10.20.22.2.38:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "47519-4": {
            "display": "Procedures Section",
            "oid": "2.16.840.1.113883.10.20.22.2.7.1:2014-06-09",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
                "2.16.840.1.113883.10.20.15.2.3.45:2021-01-01": {
                    "element": "act",
                    "display": "Initial Case Report Trigger Code Procedure Activity Act",
                },
                "2.16.840.1.113883.10.20.15.2.3.46:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Procedure Activity Observation",
                },
                "2.16.840.1.113883.10.20.15.2.3.44:2021-01-01": {
                    "element": "procedure",
                    "display": "Initial Case Report Trigger Code Procedure Activity Procedure",
                },
            },
        },
        "46241-6": {
            "display": "Admission Diagnosis Section",
            "oid": "2.16.840.1.113883.10.20.22.2.43:2015-08-01",
            "trigger_codes": {},
        },
        "11369-6": {
            "display": "Immunizations Section",
            "oid": "2.16.840.1.113883.10.20.22.2.2.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.38:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Immunization Medication Information",
                },
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                },
            },
        },
        "11535-2": {
            "display": "Discharge Diagnosis Section",
            "oid": "2.16.840.1.113883.10.20.22.2.24:2015-08-01",
            "trigger_codes": {},
        },
        "30954-2": {
            "display": "Results Section",
            "oid": "2.16.840.1.113883.10.20.22.2.3.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.35:2022-05-01": {
                    "element": "organizer",
                    "display": "Initial Case Report Trigger Code Result Organizer",
                },
                "2.16.840.1.113883.10.20.15.2.3.2:2019-04-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Result Observation",
                },
            },
        },
        "42346-7": {
            "display": "Admission Medications Section",
            "oid": "2.16.840.1.113883.10.20.22.2.44:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.36:2019-04-01": {
                    "element": "manufacturedProduct",
                    "display": "Initial Case Report Trigger Code Medication Information",
                }
            },
        },
        "11348-0": {
            "display": "Past Medical History",
            "oid": "2.16.840.1.113883.10.20.22.2.20:2015-08-01",
            "trigger_codes": {},
        },
        "8716-3": {
            "display": "Vital Signs Section",
            "oid": "2.16.840.1.113883.10.20.22.2.4.1:2015-08-01",
            "trigger_codes": {},
        },
        "11450-4": {
            "display": "Problem Section",
            "oid": "2.16.840.1.113883.10.20.22.2.5.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.3:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Problem Observation",
                }
            },
        },
        "29762-2": {
            "display": "Social History Section",
            "oid": "2.16.840.1.113883.10.20.22.2.17:2015-08-01",
            "trigger_codes": {},
        },
        "46240-8": {
            "display": "Encounters Section",
            "oid": "2.16.840.1.113883.10.20.22.2.22.1:2015-08-01",
            "trigger_codes": {
                "2.16.840.1.113883.10.20.15.2.3.3:2021-01-01": {
                    "element": "observation",
                    "display": "Initial Case Report Trigger Code Problem Observation",
                }
            },
        },
        "90767-5": {
            "display": "Pregnancy Section",
            "oid": "2.16.840.1.113883.10.20.22.2.80:2018-04-01",
            "trigger_codes": {},
        },
        "83910-0": {
            "display": "Emergency Outbreak Information Section",
            "oid": "2.16.840.1.113883.10.20.15.2.2.4:2021-01-01",
            "trigger_codes": {},
        },
        "88085-6": {
            "display": "Reportability Response Information Section",
            "oid": "2.16.840.1.113883.10.20.15.2.2.5:2021-01-01",
            "trigger_codes": {},
        },
    },
}


# NOTE:
# SERVICE FUNCTIONS
# =============================================================================


def detect_eicr_version(xml_root: _Element) -> EicrVersion:
    """
    Inspects the XML header to determine the eICR version (e.g. "1.1", "3.1").

    Defaults to "1.1" if detection fails.
    """

    # search for the specific templateId that indicates the version
    template_id = xml_root.find(
        'cda:templateId[@root="2.16.840.1.113883.10.20.15.2"]',
        namespaces=NAMESPACES,
    )

    if template_id is not None:
        version_date = template_id.get("extension")
        if version_date and version_date in EICR_VERSION_MAP:
            return EICR_VERSION_MAP[version_date]

    return "1.1"


def load_spec(version: EicrVersion) -> EICRSpecification:
    """
    Loads the static configuration for a specific eICR version.

    Loads and converts the configuration data into a strongly-typed
    EICRSpecification.
    """

    raw_data = EICR_SPECS_DATA.get(version)

    if not raw_data:
        # fallback to 1.1 if the requested version isn't found in our lookups
        # this prevents crashes for unknown versions while we expand support
        raw_data = EICR_SPECS_DATA["1.1"]
        version = "1.1"

    sections: dict[str, SectionSpecification] = {}

    for loinc, section_data in raw_data.items():
        # 1. build the list of TriggerCode objects
        trigger_codes = []
        raw_triggers = section_data.get("trigger_codes", {})

        for composite_oid, trigger_details in raw_triggers.items():
            trigger_codes.append(
                TriggerCode(
                    oid=composite_oid,
                    display_name=trigger_details.get("display", "Unknown Trigger"),
                    element_tag=trigger_details.get("element", ""),
                )
            )

        # 2. build the SectionSpecification
        spec = SectionSpecification(
            loinc_code=loinc,
            display_name=section_data.get("display", "Unknown Section"),
            template_id=section_data.get("oid", ""),
            trigger_codes=trigger_codes,
        )
        sections[loinc] = spec

    return EICRSpecification(version=version, sections=sections)

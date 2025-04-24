import json
import pathlib
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from chardet import detect
from fastapi import HTTPException, UploadFile, status


def read_json_from_assets(filename: str) -> dict:
    """
    Reads a JSON file from the assets directory.

    :param filename: The name of the file to read.
    :return: A dictionary containing the contents of the file.
    """
    return json.load(open(pathlib.Path(__file__).parent.parent / "assets" / filename))


def load_section_loincs(loinc_json: dict) -> tuple[list, dict]:
    """
    Reads section LOINC json to create two constants needed for parsing
    section data and creating refined sections.
    :param loinc_dict: Nested dictionary containing the nested section LOINCs
    :return: a list of all section LOINCs currently supported by the API;
             a dictionary of all required section LOINCs to pass validation
    """
    # LOINC codes for eICR sections our refiner API accepts
    section_list = list(loinc_json.keys())

    # dictionary of the required eICR sections'
    # LOINC section code, root templateId and extension, displayName, and title
    # to be used to create minimal sections and trigger code templates to support validation
    section_details = {
        loinc: {
            "minimal_fields": details.get("minimal_fields"),
            "trigger_code_template": details.get("trigger_code_template"),
        }
        for loinc, details in loinc_json.items()
        if details.get("required")
    }
    return (section_list, section_details)


def create_clinical_services_dict(
    clinical_services_list: list[dict],
) -> dict[str, list[str]]:
    """
    Transform the original Trigger Code Reference API response to have keys as systems
    and values as lists of codes, while ensuring the systems are recognized and using their
    shorthand names so that we can both dynamically construct XPaths and post-filter matches
    to system name varients.
    """
    system_dict = {
        "http://hl7.org/fhir/sid/icd-9-cm": "icd9",
        "http://hl7.org/fhir/sid/icd-10-cm": "icd10",
        "http://snomed.info/sct": "snomed",
        "http://loinc.org": "loinc",
        "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm",  # TODO
        "http://hl7.org/fhir/sid/cvx": "cvx",  # TODO
    }

    transformed_dict = {}
    for clinical_services in clinical_services_list:
        for service_type, entries in clinical_services.items():
            for entry in entries:
                system = entry.get("system")
                if system not in system_dict.keys():
                    raise KeyError(
                        f"{system} not a recognized clinical service system."
                    )
                shorthand_system = system_dict[system]
                if shorthand_system not in transformed_dict:
                    transformed_dict[shorthand_system] = []
                transformed_dict[shorthand_system].extend(entry.get("codes", []))
    return transformed_dict


async def read_zip(file: UploadFile) -> tuple[str, str]:
    """
    Given a zip file containing CDA_eICR.xml and CDA_RR.xml files,
    this function will read each file and return the contents as a tuple
    """
    try:
        # Read the uploaded ZIP file
        zip_bytes = await file.read()
        zip_stream = BytesIO(zip_bytes)

        # Open ZIP archive
        with ZipFile(zip_stream, "r") as z:
            # Extract relevant XML files
            eicr_xml = None
            rr_xml = None

            for filename in z.namelist():
                # Skip macOS resource fork files
                if filename.startswith("__MACOSX/") or filename.startswith("._"):
                    continue

                content = z.read(filename)
                encoding = detect(content)["encoding"]
                decoded = content.decode(encoding or "utf-8")

                if filename.endswith("CDA_eICR.xml"):
                    eicr_xml = decoded
                elif filename.endswith("CDA_RR.xml"):
                    rr_xml = decoded  # noqa

            if not eicr_xml:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CDA_eICR.xml not found in ZIP.",
                )

            return eicr_xml, rr_xml
    except BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zip file. Zip must contain a 'CDA_eICR.xml' and 'CDA_RR.xml' pair.",
        )

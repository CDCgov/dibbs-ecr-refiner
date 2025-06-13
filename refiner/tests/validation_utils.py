from pathlib import Path  # For robust and platform-independent path manipulation

from lxml import (
    etree,  # For parsing SVRL XML (could also be used for input XML if not using Saxon's parser)
)
from saxonche import (
    PySaxonProcessor,  # The core library for performing XSLT transformations (Schematron)
)

# utility functions for validating xml documents (e.g., eICR, RR) against schematron rules
#
# this module provides capabilities to:
# -> * determine the correct schematron file to use based on document type
# -> * parse svrl (schematron validation reporting language) output into a structured format
# -> * perform the actual validation of an xml string using a specified schematron
#   -> * we're going with strings so that this works better in ci and so we don't have to write files anywhere

# configuration: paths to schematron xslt assets
# -> * these xslt assets are produced via the transformation
#      script tests/assets/schemas/convert-sch-to-xslt.py
# BASE_TEST_DIR points to the 'tests' directory
# -> * __file__ is the path to this current python file (validation_utils.py)
# -> * .parent navigates up one directory level.
BASE_TEST_DIR = Path(__file__).parent

# path to the pre-compiled xslt for eICR schematron validation.
EICR_SCHEMATRON_XSLT_PATH = (
    BASE_TEST_DIR
    / "assets"  # Assumes an 'assets' subdirectory within BASE_TEST_DIR
    / "schemas"
    / "eicr"
    / "CDAR2_IG_PHCASERPT_R2_STU1.1_SCHEMATRON.xsl"
)
# path to the pre-compiled xslt for RR schematron validation.
RR_SCHEMATRON_XSLT_PATH = (
    BASE_TEST_DIR
    / "assets"
    / "schemas"
    / "rr"
    / "CDAR2_IG_PHCR_R2_RR_D1_2017DEC_SCHEMATRON.xsl"
)


def determine_document_type_and_schematron(
    xml_content_string: str, doc_type_hint: str = "eicr"
) -> tuple[str, str]:
    """
    Determines the appropriate Schematron XSLT file path based on a document type hint.

    Currently, this function relies solely on the `doc_type_hint`. A more advanced
    implementation might inspect the `xml_content_string` for specific elements or
    LOINC codes to automatically determine the document type if the hint is unreliable
    or absent.

    Args:
        xml_content_string: The XML content as a string. (Currently unused for detection logic).
        doc_type_hint: A string indicating the document type, e.g., "eicr" or "rr".
                       Defaults to "eicr". Case-insensitive.

    Returns:
        A tuple containing:
            - str: The determined document type name (e.g., "eicr", "rr").
            - str: The absolute string path to the corresponding Schematron XSLT file.

    Raises:
        FileNotFoundError: If the Schematron XSLT file for the determined type cannot be found.
        ValueError: If the `doc_type_hint` is not recognized or unsupported.
    """

    doc_type_hint_lower = doc_type_hint.lower()

    if doc_type_hint_lower == "eicr":
        if not EICR_SCHEMATRON_XSLT_PATH.is_file():
            # critical error if the required schematron asset is missing
            raise FileNotFoundError(
                f"eICR Schematron XSLT not found at {EICR_SCHEMATRON_XSLT_PATH}"
            )
        return "eicr", str(EICR_SCHEMATRON_XSLT_PATH)
    elif doc_type_hint_lower == "rr":
        if not RR_SCHEMATRON_XSLT_PATH.is_file():
            raise FileNotFoundError(
                f"RR Schematron XSLT not found at {RR_SCHEMATRON_XSLT_PATH}"
            )
        return "rr", str(RR_SCHEMATRON_XSLT_PATH)
    else:
        # if the hint doesn't match known types, raise an error
        raise ValueError(
            f"Unsupported document type hint: '{doc_type_hint}'. Expected 'eicr' or 'rr'."
        )


def parse_svrl_string(svrl_string: str) -> list[dict]:
    """
    Parses a Schematron Validation Reporting Language (SVRL) XML string.

    Extracts detailed validation messages (errors, warnings, informational messages)
    from the SVRL report into a structured list of dictionaries.

    Args:
        svrl_string: The SVRL report content as an XML string.

    Returns:
        A list of dictionaries. Each dictionary represents a single validation
        message and typically includes keys like 'severity', 'message', 'context',
        'test', 'id', and 'role'. Returns an empty list if the svrl_string is empty.

    Raises:
        ValueError: If the `svrl_string` cannot be parsed as valid XML.
    """

    if not svrl_string:  # Handle cases where an empty SVRL string might be passed
        return []

    try:
        # parse the svrl string using lxml.etree
        # -> * svrl is xml, so it needs to be parsed before interrogation
        # -> * .encode('utf-8') is used as fromstring expects bytes
        svrl_doc = etree.fromstring(svrl_string.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        # if the svrl isn't well-formed xml; it's a critical issue with the validation output
        raise ValueError(
            f"Failed to parse SVRL string as XML: {e}. SVRL content (first 500 chars): '{svrl_string[:500]}...'"
        ) from e

    # define the svrl namespace for XPath queries.
    ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
    results = []

    # xpath to find all 'failed-assert' (errors/warnings) and 'successful-report' (often infos) elements.
    # these elements contain the details of individual Schematron rule outcomes.
    for assertion in svrl_doc.xpath(
        ".//svrl:failed-assert | .//svrl:successful-report", namespaces=ns
    ):
        text_element = assertion.find("svrl:text", namespaces=ns)
        # extract the human-readable message from the assertion.
        message = (
            text_element.text.strip()
            if text_element is not None and text_element.text is not None
            else "No message provided in SVRL assertion."
        )

        # determine the severity of the message (ERROR, WARNING, INFO).
        severity = "UNKNOWN"  # Default severity
        if assertion.tag == "{http://purl.oclc.org/dsdl/svrl}failed-assert":
            # for failed assertions, derive severity based on keywords (SHALL, SHOULD)
            first_word = (
                # use uppercase for case-insensitive match
                message.split()[0].upper() if message else ""
            )
            if first_word == "SHALL":
                severity = "ERROR"
            elif first_word == "SHOULD" or "SHOULD CONTAIN" in message.upper():
                severity = "WARNING"
            # fallback checks if the first word wasn't decisive but keywords appear later
            elif "SHALL" in message.upper() and "SHOULD" not in message.upper():
                severity = "ERROR"
            elif "SHOULD" in message.upper():
                severity = "WARNING"
            else:
                # default for a failed assertion if not clearly specified by keywords
                severity = "ERROR"
        elif assertion.tag == "{http://purl.oclc.org/dsdl/svrl}successful-report":
            # successful reports are often informational but can be configured via 'role'.
            # keywords like "MAY" also often indicate informational messages
            if assertion.get("role") == "information" or message.upper().startswith(
                "MAY"
            ):
                severity = "INFO"
            else:
                # default for successful reports
                severity = "INFO"

        # append a dictionary of the parsed assertion details to the results list
        results.append(
            {
                "severity": severity,
                "message": message,
                "context": assertion.get(
                    # xpath location of the issue in the validated xml
                    "location",
                    "No context provided",
                ),
                "test": assertion.get(
                    # the schematron <assert> or <report> test expression
                    "test",
                    "No test condition provided",
                ),
                "id": assertion.get(
                    # the id of the schematron rule or assertion
                    "id",
                    "No ID provided",
                ),
                "role": assertion.get(
                    # the 'role' attribute from the SVRL (e.g., 'error', 'warning', 'information')
                    "role"
                ),
            }
        )
    return results


def validate_xml_string(xml_content_string: str, doc_type_hint: str = "eicr") -> dict:
    """
    Validates an XML content string against the appropriate Schematron rules.

    This is the main validation function. It orchestrates the process:
    1. Determines the correct Schematron XSLT to use.
    2. Initializes the Saxon XSLT processor.
    3. Compiles the Schematron XSLT.
    4. Parses the input XML string into Saxon's internal XDM format.
    5. Transforms the XDM using the compiled Schematron to produce an SVRL report.
    6. Parses the SVRL report to count errors, warnings, and infos, and collect details.

    Args:
        xml_content_string: The XML data to be validated, as a string.
        doc_type_hint: A hint for the document type (e.g., "eicr", "rr") to select
                       the correct Schematron. Defaults to "eicr".

    Returns:
        A dictionary summarizing the validation outcome:
            - "errors" (int): Count of error messages.
            - "warnings" (int): Count of warning messages.
            - "infos" (int): Count of informational messages.
            - "details" (list[dict]): A list of all parsed validation messages
                                      (from `parse_svrl_string`).
            - "raw_svrl" (str | None): The raw SVRL output string. Can be None if
                                       the transformation process fails before SVRL generation.
    """

    # initialize the structure for the validation summary
    validation_summary = {
        "errors": 0,
        "warnings": 0,
        "infos": 0,
        "details": [],
        "raw_svrl": None,  # Store the raw SVRL for debugging if needed
    }

    # handle empty input XML string immediately
    if not xml_content_string:
        validation_summary["details"].append(
            {
                "severity": "ERROR",
                "message": "Input XML content string is empty.",
                "context": "Input Validation",
                "test": "Content Check",
                "id": "INPUT_EMPTY",
                "role": "critical",
            }
        )
        validation_summary["errors"] = 1
        return validation_summary

    try:
        # determine the document type and the path to the corresponding Schematron xslt
        doc_type, xslt_path = determine_document_type_and_schematron(
            xml_content_string, doc_type_hint
        )

        # PySaxonProcessor needs to be used within a 'with' statement to ensure resources are managed
        # -> * 'license=False' uses Saxon HE (Home Edition), which is open-source
        # -> * this is the only library we're aware of that can do this work
        with PySaxonProcessor(license=False) as proc:
            # create an xslt 3.0 processor
            xslt_processor = proc.new_xslt30_processor()

            try:
                # compile the schematron xslt--this is a one-time cost per xslt if cached,
                # but here it's done per call. if more volume hits our performance we may
                # need to consider caching compiled stylesheets (we're not sure in what way
                # eICR and RR validation will be folded into the application)
                compiled_stylesheet = xslt_processor.compile_stylesheet(
                    stylesheet_file=xslt_path
                )
            except Exception as compile_err:
                # if xslt compilation fails, it's a setup or schematron file issue
                raise RuntimeError(
                    f"Failed to compile Schematron XSLT '{xslt_path}': {compile_err}"
                ) from compile_err

            # parse the input xml string into saxon's internal xdm (xml data model) format
            # -> * this is necessary because saxon was encountering errors
            try:
                xdm_document_node = proc.parse_xml(xml_text=xml_content_string)
            except Exception as parse_err:
                # if the input xml itself can't be parsed by saxon
                raise RuntimeError(
                    f"Failed to parse input XML string for Schematron validation: {parse_err}. "
                    f"XML (first 500 chars): '{xml_content_string[:500]}'"
                ) from parse_err

            # perform the xslt transformation using the compiled stylesheet and the xdm node of the input xml
            # the output of this transformation is the svrl report
            try:
                svrl_result_string = compiled_stylesheet.transform_to_string(
                    xdm_node=xdm_document_node
                )
                validation_summary["raw_svrl"] = (
                    svrl_result_string  # Store for potential debugging
                )
            except Exception as transform_err:
                # if the transformation itself fails
                raise RuntimeError(
                    f"Schematron transformation failed for doc_type '{doc_type}': {transform_err}."
                ) from transform_err

            # if an svrl result string was produced, parse it
            if svrl_result_string:
                parsed_messages = parse_svrl_string(svrl_result_string)
                validation_summary["details"] = parsed_messages
                # tally errors, warnings, and infos from the parsed messages
                for msg in parsed_messages:
                    if msg["severity"] == "ERROR":
                        validation_summary["errors"] += 1
                    elif msg["severity"] == "WARNING":
                        validation_summary["warnings"] += 1
                    elif msg["severity"] == "INFO":
                        validation_summary["infos"] += 1
            else:
                # an empty svrl string might mean no rules fired or no validation issues,
                # depending on the schematron. no action needed here; counts remain 0
                pass

    # exception handling for the validation process
    # -> * catch specific, anticipated errors to provide more context
    except (
        FileNotFoundError
    ) as fnf_err:  # Raised by determine_document_type_and_schematron
        validation_summary["details"].append(
            {
                "severity": "ERROR",
                "message": str(fnf_err),
                "context": "Setup",
                "test": "Schematron File Check",
                "id": "SCHEMATRON_MISSING",
                "role": "critical",
            }
        )
        validation_summary["errors"] = 1
    except (
        ValueError
    ) as val_err:  # Raised by determine_document_type or parse_svrl_string
        validation_summary["details"].append(
            {
                "severity": "ERROR",
                "message": str(val_err),
                "context": "Input/Parsing",
                "test": "Data Validity Check",
                "id": "INVALID_INPUT_OR_SVRL",
                "role": "critical",
            }
        )
        validation_summary["errors"] = 1
    except RuntimeError as rt_err:
        validation_summary["details"].append(
            {
                "severity": "ERROR",
                "message": str(rt_err),
                "context": "Validation Process",
                "test": "Schematron Engine Execution",
                "id": "VALIDATION_RUNTIME_ERROR",
                "role": "critical",
            }
        )
        validation_summary["errors"] = 1
    except Exception as e:
        validation_summary["details"].append(
            {
                "severity": "ERROR",
                "message": f"An unexpected error occurred during validation: {e}",
                "context": "General Execution",
                "test": "Overall Validation Process",
                "id": "UNEXPECTED_VALIDATION_ERROR",
                "role": "critical",
            }
        )
        validation_summary["errors"] = 1

    return validation_summary

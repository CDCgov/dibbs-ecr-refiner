from typing import Annotated

from fastapi import APIRouter, File, Query, Request, Response, UploadFile, status

from ...core.examples import ECR_RESPONSE_EXAMPLES
from ...core.models import RefineECRResponse
from ...services.refine import refine, validate_message, validate_sections_to_include
from ...services.rr_parser import get_reportable_conditions, parse_xml
from ...services.terminology import _get_clinical_services
from ...services.utils import (
    create_clinical_services_dict,
    read_zip,
)

# create a router instance for this file
router = APIRouter(prefix="/ecr")


@router.post(
    "/zip-upload",
    status_code=200,
    summary="Refine eCR from ZIP",
)
async def refine_ecr_from_zip(
    file: UploadFile = File(...),
    sections_to_include: Annotated[
        str | None,
        Query(
            description="""The sections of an ECR to include in the refined message.
                Multiples can be delimited by a comma. Valid LOINC codes for sections are:\n
                46240-8: Encounters--Hospitalizations+outpatient visits narrative\n
                10164-2: History of present illness\n
                11369-6: History of immunizations\n
                29549-3: Medications administered\n
                18776-5: Plan of treatment: Care plan\n
                11450-4: Problem--Reported list\n
                29299-5: Reason for visit\n
                30954-2: Results--Diagnostic tests/laboratory data narrative\n
                29762-2: Social history--Narrative\n
                """
        ),
    ] = None,
    conditions_to_include: Annotated[
        str | None,
        Query(
            description="The SNOMED condition codes to use to search for relevant clinical services in the ECR."
            + " Multiples can be delimited by a comma."
        ),
    ] = None,
) -> Response:
    """
    Accepts a ZIP file, extracts `CDA_eICR.xml` and `CDA_RR.xml`,
    and processes them for refining the eCR message.

    - `file`: The uploaded ZIP file.
    - `sections_to_include`: Comma-separated LOINC codes for filtering eCR sections.
    - `conditions_to_include`: Comma-separated SNOMED condition codes.

    Returns:
    - A refined XML eCR response.
    """
    eicr_xml, _rr_xml = await read_zip(file)

    # Process the extracted XML
    validated_message, error_message = validate_message(eicr_xml)
    if error_message:
        return Response(content=error_message, status_code=status.HTTP_400_BAD_REQUEST)

    # Parse the RR XML
    _rr_xml = parse_xml(_rr_xml)

    if isinstance(_rr_xml, Response):
        return _rr_xml

    reportable_snomeds = get_reportable_conditions(_rr_xml)

    if not conditions_to_include:
        if reportable_snomeds:
            conditions_to_include = reportable_snomeds

    sections = None
    if sections_to_include:
        sections, error_message = validate_sections_to_include(sections_to_include)
        if error_message:
            return Response(
                content=error_message,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    clinical_services = None
    if conditions_to_include:
        clinical_services = [
            service for service in _get_clinical_services(conditions_to_include)
        ]

        # create a simple dictionary structure for refine.py to consume
        clinical_services = create_clinical_services_dict(clinical_services)

    # Refine the extracted eICR data
    refined_data = refine(validated_message, sections, clinical_services)

    return Response(content=refined_data, media_type="application/xml")


@router.post(
    "",
    response_model=RefineECRResponse,
    status_code=200,
    responses=ECR_RESPONSE_EXAMPLES,
    summary="Refine eCR",
)
async def refine_ecr(
    refiner_input: Request,
    sections_to_include: Annotated[
        str | None,
        Query(
            description="""The sections of an ECR to include in the refined message.
            Multiples can be delimited by a comma. Valid LOINC codes for sections are:\n
            46240-8: Encounters--Hospitalizations+outpatient visits narrative\n
            10164-2: History of present illness\n
            11369-6: History of immunizations\n
            29549-3: Medications administered\n
            18776-5: Plan of treatment: Care plan\n
            11450-4: Problem--Reported list\n
            29299-5: Reason for visit\n
            30954-2: Results--Diagnostic tests/laboratory data narrative\n
            29762-2: Social history--Narrative\n
            """
        ),
    ] = None,
    conditions_to_include: Annotated[
        str | None,
        Query(
            description="The SNOMED condition codes to use to search for relevant clinical services in the ECR."
            + " Multiples can be delimited by a comma."
        ),
    ] = None,
) -> Response:
    """
    This endpoint refines an incoming XML eCR message based on sections to include and/or trigger code
    conditions to include, based on the parameters included in the endpoint.

    The return will be a formatted, refined XML, limited to just the data specified.

    ### Inputs and Outputs
    - :param refiner_input: The request object containing the XML input.
    - :param sections_to_include: The fields to include in the refined message.
    - :param conditions_to_include: The SNOMED condition codes to use to search for
      relevant clinical services in the eCR.
    - :return: The RefineeCRResponse, the refined XML as a string.
    """
    data = await refiner_input.body()

    validated_message, error_message = validate_message(data)
    if error_message:
        return Response(content=error_message, status_code=status.HTTP_400_BAD_REQUEST)

    sections = None
    if sections_to_include:
        sections, error_message = validate_sections_to_include(sections_to_include)
        if error_message:
            return Response(
                content=error_message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

    clinical_services = None
    if conditions_to_include:
        clinical_services = [
            service for service in _get_clinical_services(conditions_to_include)
        ]

        # create a simple dictionary structure for refine.py to consume
        clinical_services = create_clinical_services_dict(clinical_services)

    data = refine(validated_message, sections, clinical_services)

    return Response(content=data, media_type="application/xml")

import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, Query, Request, Response, UploadFile, status
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.base_service import BaseService
from app.db import get_value_sets_for_condition
from app.models import RefineECRResponse
from app.refine import refine, validate_message, validate_sections_to_include
from app.rr_parser import get_reportable_conditions, parse_xml
from app.utils import create_clinical_services_dict, read_json_from_assets, read_zip

from .routes import demo

is_production = os.getenv("PRODUCTION", "false").lower() == "true"

# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="Message Refiner",
    service_path="/message-refiner",
    description_path=Path(__file__).parent.parent / "README.md",
    include_health_check_endpoint=False,
    openapi_url="/message-refiner/openapi.json",
).start()

router = APIRouter(prefix="/api")
router.include_router(demo.router)

# /api/ecr endpoint request examples
refine_ecr_request_examples = read_json_from_assets("sample_refine_ecr_request.json")
refine_ecr_response_examples = read_json_from_assets("sample_refine_ecr_response.json")


def custom_openapi() -> dict[str, Any]:
    """
    Customize FastAPI OpenAPI response to support example requests.

    Modifies the OpenAPI schema to allow example requests where raw Request
    objects cannot have annotations.

    Returns:
        dict[str, Any]: Customized OpenAPI schema.
    """

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    path = openapi_schema["paths"]["/api/ecr"]["post"]
    path["requestBody"] = {
        "content": {
            "application/xml": {
                "schema": {"type": "Raw eCR XML payload"},
                "examples": refine_ecr_request_examples,
            }
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@router.get("/healthcheck")
async def health_check() -> dict[str, str]:
    """
    Check service health status.

    Returns:
        dict[str, str]: Service status response:
            - {"status": "OK"} with HTTP 200 if service is healthy
    """

    return {"status": "OK"}


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
    Process and refine an eCR message from uploaded ZIP file.

    Extracts CDA_eICR.xml and CDA_RR.xml from the uploaded ZIP file and
    refines the eCR message based on specified sections and conditions.

    Args:
        file: ZIP file containing CDA_eICR.xml and CDA_RR.xml.
        sections_to_include: Comma-separated LOINC codes for filtering eCR sections.
        conditions_to_include: Comma-separated SNOMED condition codes for filtering.

    Returns:
        Response: The refined XML eCR document.
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
        clinical_services = list(_get_clinical_services(conditions_to_include))

        # create a simple dictionary structure for refine.py to consume
        clinical_services = create_clinical_services_dict(clinical_services)

    # Refine the extracted eICR data
    refined_data = refine(validated_message, sections, clinical_services)

    return Response(content=refined_data, media_type="application/xml")


@router.post(
    "/ecr",
    response_model=RefineECRResponse,
    status_code=200,
    responses=refine_ecr_response_examples,
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
    Refine an XML eCR message based on specified sections and conditions.

    Takes an XML eCR message and refines it by filtering sections and clinical
    services based on provided parameters. Returns a formatted XML limited to
    the specified data.

    Args:
        refiner_input: Request object containing the XML input.
        sections_to_include: Comma-separated LOINC codes for filtering eCR sections.
            Valid codes include:
            - 46240-8: Encounters--Hospitalizations+outpatient visits
            - 10164-2: History of present illness
            - 11369-6: History of immunizations
            - 29549-3: Medications administered
            - 18776-5: Plan of treatment
            - 11450-4: Problem list
            - 29299-5: Reason for visit
            - 30954-2: Results--Diagnostic tests/laboratory
            - 29762-2: Social history
        conditions_to_include: Comma-separated SNOMED condition codes for
            searching relevant clinical services.

    Returns:
        Response: The refined XML eCR document.
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
        clinical_services = list(_get_clinical_services(conditions_to_include))

        # create a simple dictionary structure for refine.py to consume
        clinical_services = create_clinical_services_dict(clinical_services)

    data = refine(validated_message, sections, clinical_services)

    return Response(content=data, media_type="application/xml")


def _get_clinical_services(condition_codes: str) -> list[dict]:
    """
    Get clinical services associated with provided condition codes.

    Queries the TES database to find and return all clinical services
    associated with the given SNOMED condition codes.

    Args:
        condition_codes: Comma-separated SNOMED condition codes to look up.

    Returns:
        list[dict]: Clinical services associated with the condition codes.
            Each dictionary contains the service details.
    """

    clinical_services_list = []
    conditions_list = condition_codes.split(",")
    for condition in conditions_list:
        clinical_services_list.append(get_value_sets_for_condition(condition))
    return clinical_services_list


app.include_router(router)

# When running the application in production we will mount the static client files from the
# "dist" directory. This directory will typically not exist during development since the client
# runs separately in its own Docker container.
if is_production:
    app.mount(
        "/",
        StaticFiles(directory="dist", html=True, check_dir=is_production),
        name="dist",
    )

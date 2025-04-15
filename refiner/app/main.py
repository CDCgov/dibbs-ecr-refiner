import chardet
import io
from pathlib import Path
from fastapi import Query, Request, Response, status, UploadFile, File
from fastapi.openapi.utils import get_openapi
from typing import Annotated, Optional
import zipfile

from app.base_service import BaseService
from app.db import get_value_sets_for_condition
from app.models import RefineECRResponse
from app.refine import refine, validate_message, validate_sections_to_include
from app.utils import create_clinical_services_dict, read_json_from_assets

# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="Message Refiner",
    service_path="/message-refiner",
    description_path=Path(__file__).parent.parent / "README.md",
    include_health_check_endpoint=False,
    openapi_url="/message-refiner/openapi.json",
).start()


# /ecr endpoint request examples
refine_ecr_request_examples = read_json_from_assets("sample_refine_ecr_request.json")
refine_ecr_response_examples = read_json_from_assets("sample_refine_ecr_response.json")


def custom_openapi():
    """
    This customizes the FastAPI response to allow example requests given that the
    raw Request cannot have annotations.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    path = openapi_schema["paths"]["/ecr"]["post"]
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


@app.get("/")
async def health_check():
    """
    This endpoint checks service status. If an HTTP 200 status code is returned
    along with `{"status": "OK"}'` then the Message Refiner is available and
    running properly.
    """
    return {"status": "OK"}


@app.post(
    "/zip-upload",
    status_code=200,
    summary="Refine eCR from ZIP",
)
async def refine_ecr_from_zip(
    file: UploadFile = File(...),
    sections_to_include: Optional[str] = Query(
        None, description="Comma-separated LOINC codes to filter eCR sections."
    ),
    conditions_to_include: Optional[str] = Query(
        None, description="Comma-separated SNOMED condition codes."
    ),
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

    try:
        # Read the uploaded ZIP file
        zip_bytes = await file.read()
        zip_stream = io.BytesIO(zip_bytes)

        # Open ZIP archive
        with zipfile.ZipFile(zip_stream, "r") as z:
            # Extract relevant XML files
            eicr_xml = None
            rr_xml = None

            for filename in z.namelist():
                try:
                    # Skip macOS resource fork files
                    if filename.startswith("__MACOSX/") or filename.startswith("._"):
                        continue

                    content = z.read(filename)
                    encoding = chardet.detect(content)["encoding"]
                    decoded = content.decode(encoding or "utf-8")

                    if filename.endswith("CDA_eICR.xml"):
                        eicr_xml = decoded
                    elif filename.endswith("CDA_RR.xml"):
                        rr_xml = decoded  # noqa
                except Exception as e:
                    return Response(
                        content=f"Failed to decode {filename}: {str(e)}",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

            #             if not eicr_xml:
            #                 return Response(content="CDA_eICR.xml not found in ZIP.", status_code=status.HTTP_400_BAD_REQUEST)

            # Process the extracted XML
            validated_message, error_message = validate_message(eicr_xml)
            if error_message:
                return Response(
                    content=error_message, status_code=status.HTTP_400_BAD_REQUEST
                )

            sections = None
            if sections_to_include:
                sections, error_message = validate_sections_to_include(
                    sections_to_include
                )
                if error_message:
                    return Response(
                        content=error_message,
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

            clinical_services = None
            if conditions_to_include:
                responses = await _get_clinical_services(conditions_to_include)
                if set([response.status_code for response in responses]) != {200}:
                    error_message = ";".join(
                        [
                            str(response)
                            for response in responses
                            if response.status_code != 200
                        ]
                    )
                    return Response(
                        content=error_message, status_code=status.HTTP_502_BAD_GATEWAY
                    )
                clinical_services = [response.json() for response in responses]
                clinical_services = create_clinical_services_dict(clinical_services)

            # Refine the extracted eICR data
            refined_data = refine(validated_message, sections, clinical_services)

            return Response(content=refined_data, media_type="application/xml")

    except zipfile.BadZipFile:
        return Response(
            content="Invalid ZIP file.", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            content=f"Error processing file: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.post(
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


def _get_clinical_services(condition_codes: str) -> list[dict]:
    """
    This a function that loops through the provided condition codes. For each
    condition code provided, it returns the value set of clinical services associated
    with that condition.

    :param condition_codes: SNOMED condition codes to look up in the TES DB
    :return: List of clinical services associated with a condition code
    """
    clinical_services_list = []
    conditions_list = condition_codes.split(",")
    for condition in conditions_list:
        clinical_services_list.append(get_value_sets_for_condition(condition))
    return clinical_services_list

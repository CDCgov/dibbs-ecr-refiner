import io
import os
import pathlib
import zipfile
from pathlib import Path
from typing import Annotated

import chardet
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.base_service import BaseService
from app.db import get_value_sets_for_condition
from app.models import RefineECRResponse
from app.refine import refine, validate_message, validate_sections_to_include
from app.utils import create_clinical_services_dict, read_json_from_assets

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

# /api/ecr endpoint request examples
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
async def health_check():
    """
    This endpoint checks service status. If an HTTP 200 status code is returned
    along with `{"status": "OK"}'` then the Message Refiner is available and
    running properly.
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
    Accepts a ZIP file, extracts `CDA_eICR.xml` and `CDA_RR.xml`,
    and processes them for refining the eCR message.

    - `file`: The uploaded ZIP file.
    - `sections_to_include`: Comma-separated LOINC codes for filtering eCR sections.
    - `conditions_to_include`: Comma-separated SNOMED condition codes.

    Returns:
    - A refined XML eCR response.
    """
    eicr_xml, _rr_xml = await _read_zip(file)

    # Process the extracted XML
    validated_message, error_message = validate_message(eicr_xml)
    if error_message:
        return Response(content=error_message, status_code=status.HTTP_400_BAD_REQUEST)

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


def _get_demo_zip_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent / "assets" / "demo" / "monmothma.zip"


@router.get("/demo/upload")
async def demo_upload(file_path: pathlib.Path = Depends(_get_demo_zip_path)):
    """
    Grabs an eCR zip file from the file system and runs it through the upload/refine process.
    """
    try:
        # Grab the demo zip file and turn it into an UploadFile
        if not pathlib.Path(file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to find demo zip file to download.",
            )

        filename = os.path.basename(file_path)
        with open(file_path, "rb") as demo_file:
            zip_content = demo_file.read()

        file_like = io.BytesIO(zip_content)
        file_like.seek(0)
        upload_file = UploadFile(
            file=file_like,
            filename=filename,
            headers={"Content-Type": "application/zip"},
        )

        # Read the created UploadFile
        eicr_xml, _rr_xml = await _read_zip(upload_file)
        validated_message, error_message = validate_message(eicr_xml)
        refined_data = refine(validated_message, None, None)
        return Response(content=refined_data, media_type="application/xml")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process demo zip file.",
        )


@router.get("/demo/download")
async def demo_download(file_path: pathlib.Path = Depends(_get_demo_zip_path)):
    """
    Allows the user to download the sample eCR zip file.
    """
    # Grab demo zip and send it along to the client
    if not pathlib.Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to find demo zip file to download.",
        )
    filename = os.path.basename(file_path)
    return FileResponse(
        file_path, media_type="application/octet-stream", filename=filename
    )


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


async def _read_zip(file: UploadFile) -> tuple[str, str]:
    """
    Given a zip file containing CDA_eICR.xml and CDA_RR.xml files,
    this function will read each file and return the contents as a tuple
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

            if not eicr_xml:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CDA_eICR.xml not found in ZIP.",
                )

            return eicr_xml, rr_xml
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid zip file. Zip must contain a 'CDA_eICR.xml' and 'CDA_RR.xml' pair.",
        )


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

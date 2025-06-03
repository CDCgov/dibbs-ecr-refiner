from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)

from ...core.exceptions import (
    SectionValidationError,
    XMLValidationError,
    ZipValidationError,
)
from ...core.models.api import ECR_RESPONSE_EXAMPLES, RefineECRResponse
from ...core.models.types import XMLFiles
from ...services import file_io, refine

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
    Process and refine eCR messages from uploaded ZIP files.

    Accepts a ZIP file, extracts `CDA_eICR.xml` and `CDA_RR.xml`,
    and processes them for refining the eCR message.

    Args:
        file: The uploaded ZIP file.
        sections_to_include: Comma-separated LOINC codes for filtering eCR sections.
        conditions_to_include: Comma-separated SNOMED condition codes.

    Returns:
        Response: A refined XML eCR response.
    """
    try:
        # read both xml files
        xml_files = await file_io.read_xml_zip(file)

        # process RR to get reportable conditions
        rr_results = refine.process_rr(xml_files)
        reportable_conditions = rr_results["reportable_conditions"]

        # use RR conditions if none specified
        if not conditions_to_include and reportable_conditions:
            conditions_to_include = ",".join(
                condition["code"] for condition in rr_results["reportable_conditions"]
            )
        #         # use RR conditions if none specified
        #         if not conditions_to_include and reportable_conditions:
        #             conditions_to_include = reportable_conditions

        # validate sections if provided
        sections = None
        if sections_to_include:
            sections = refine.validate_sections_to_include(sections_to_include)

        # refine the eICR
        refined_data = refine.refine_eicr(xml_files, sections, conditions_to_include)

        return Response(content=refined_data, media_type="application/xml")

    except (XMLValidationError, ZipValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "details": e.details},
        )
    except SectionValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "details": e.details},
        )


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
    Refine an XML eCR message based on specified parameters.

    This endpoint refines an incoming XML eCR message based on sections to include and/or trigger code
    conditions to include, based on the parameters included in the endpoint.

    The return will be a formatted, refined XML, limited to just the data specified.

    ### Inputs and Outputs

    Args:
        refiner_input: The request object containing the XML input.
        sections_to_include: The fields to include in the refined message.
        conditions_to_include: The SNOMED condition codes to use to search for
            relevant clinical services in the eCR.

    Returns:
        Response: The RefineeCRResponse, the refined XML as a string.
    """

    try:
        # get raw xml data
        data = await refiner_input.body()

        # create XMLFiles with empty RR since this endpoint only processes eICR
        xml_files = XMLFiles(eicr=data.decode("utf-8"), rr="")

        # validate sections if provided
        sections = None
        if sections_to_include:
            sections = refine.validate_sections_to_include(sections_to_include)

        # refine the eICR
        refined_data = refine.refine_eicr(xml_files, sections, conditions_to_include)
        return Response(content=refined_data, media_type="application/xml")

    except XMLValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "details": e.details},
        )
    except SectionValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "details": e.details},
        )

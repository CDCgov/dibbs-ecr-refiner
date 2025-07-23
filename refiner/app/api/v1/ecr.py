from typing import Annotated

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
from fastapi.responses import JSONResponse

from ...core.exceptions import (
    ConditionCodeError,
    SectionValidationError,
    XMLValidationError,
    ZipValidationError,
)
from ...core.models.api import ECR_RESPONSE_EXAMPLES, RefineECRResponse
from ...core.models.types import XMLFiles
from ...db.connection import DatabaseConnection, get_db_connection
from ...services import file_io
from ...services.refiner import refine
from ...services.refiner.helpers import (
    get_condition_codes_xpath,
    get_processed_groupers_from_condition_codes,
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
    db: DatabaseConnection = Depends(get_db_connection),
) -> Response:
    """
    Process and refine eCR messages from uploaded ZIP files.

    Accepts a ZIP file, extracts `CDA_eICR.xml` and `CDA_RR.xml`,
    and processes them for refining the eCR message.

    Args:
        file: The uploaded ZIP file.
        sections_to_include: Comma-separated LOINC codes for filtering eCR sections.
        conditions_to_include: Comma-separated SNOMED condition codes.
        db: Established database connection (dependency injected)

    Returns:
        Response: A refined XML eCR response.
    """

    try:
        # read both xml files
        xml_files = await file_io.read_xml_zip(file)

        # process RR to get reportable conditions
        rr_results = refine.process_rr(xml_files)
        reportable_conditions = rr_results["reportable_conditions"]

        # if user did not provide, but RR has reportable conditions, use those
        if not conditions_to_include:
            if not reportable_conditions:
                raise ConditionCodeError(
                    "No condition codes provided to refine_eicr; at least one is required."
                )
            conditions_to_include = ",".join(
                condition["code"] for condition in reportable_conditions
            )

        # validate sections if provided
        sections = None
        if sections_to_include:
            sections = refine.validate_sections_to_include(sections_to_include)

        condition_eicr_pairs = refine.build_condition_eicr_pairs(
            xml_files, reportable_conditions
        )

        # Store results
        refined_results = []

        # for each reportable condition, use a separate XMLFiles copy and refine for that condition.
        # this approach guarantees that each output eICR is isolated and scoped to a single reportable condition,
        # which avoids data leakage between conditions and makes future per-condition processing (such as RR outputs)
        # straightforward.
        for pair in condition_eicr_pairs:
            condition = pair["reportable_condition"]
            # each pair holds a distinct XMLFiles instance
            xml_files = pair["xml_files"]

            # refine the eICR for the specific condition code.
            condition_code = condition["code"]
            processed_groupers = get_processed_groupers_from_condition_codes(
                condition_codes=condition_code, db=db
            )

            condition_codes_xpath = get_condition_codes_xpath(processed_groupers)
            refined_eicr = refine.refine_eicr(
                xml_files=xml_files,
                condition_codes_xpath=condition_codes_xpath,
                sections_to_include=sections,
            )

            refined_results.append(
                {
                    "reportable_condition": condition,
                    "refined_eicr": refined_eicr,
                }
            )

        # Return all refined eICRs and their conditions
        return JSONResponse(content=refined_results)

    except (XMLValidationError, ZipValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "details": e.details},
        )
    except ConditionCodeError as e:  # <-- this must be here
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
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
    db: DatabaseConnection = Depends(get_db_connection),
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
        db: Established database connection (dependency injected)

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

        # REQUIRE conditions_to_include for plain eCR (no RR to fallback on!)
        if not conditions_to_include:
            raise ConditionCodeError(
                "No condition codes provided to refine_eicr; at least one is required."
            )

        condition_code = conditions_to_include
        processed_groupers = get_processed_groupers_from_condition_codes(
            condition_codes=condition_code, db=db
        )

        condition_codes_xpath = get_condition_codes_xpath(processed_groupers)

        # refine the eICR
        refined_data = refine.refine_eicr(
            xml_files=xml_files,
            condition_codes_xpath=condition_codes_xpath,
            sections_to_include=sections,
        )
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
    except ConditionCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )

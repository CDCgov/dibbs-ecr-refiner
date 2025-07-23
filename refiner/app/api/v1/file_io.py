from fastapi import APIRouter, HTTPException, UploadFile, status

from ...core.exceptions import (
    ECRRefinementError,
    FileProcessingError,
    SectionValidationError,
    XMLProcessingError,
    XMLValidationError,
    ZipValidationError,
)
from ...core.models.api import XMLUploadResponse
from ...services import file_io
from ...services.refiner import refine

router = APIRouter()


@router.post("/upload/xml-zip", response_model=XMLUploadResponse)
async def process_xml_zip(file: UploadFile) -> XMLUploadResponse:
    """
    Process a ZIP file containing eICR and RR XML documents.

    Returns:
        XMLUploadResponse: Processed XML content and extracted data

    Raises:
        HTTPException: With appropriate status code and error details
    """

    try:
        # read both files
        xml_files = await file_io.read_xml_zip(file)

        # process both documents
        refined_eicr = refine.refine_eicr(xml_files=xml_files, condition_codes_xpath="")
        rr_results = refine.process_rr(xml_files)

        return XMLUploadResponse(
            eicr=refined_eicr,
            rr=xml_files.rr,
            reportable_conditions=rr_results["reportable_conditions"],
        )

    except ZipValidationError as e:
        # invalid zip file or missing required files
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e.message), "details": e.details},
        )

    except XMLValidationError as e:
        # invalid xml content
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e.message), "details": e.details},
        )

    except XMLProcessingError as e:
        # xml parsing failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e.message), "details": e.details},
        )

    except (ECRRefinementError, SectionValidationError) as e:
        # refining failed for this document(s) or in a specific section
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e.message), "details": e.details},
        )

    except FileProcessingError as e:
        # general file processing errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(e.message), "details": e.details},
        )

    except Exception as e:
        # unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An unexpected error occurred",
                "details": {"error": str(e)},
            },
        )

from refiner.app.db.demo.model import IndependentTestUploadResponse


def test_response_html_files_field() -> None:
    """
    Ensure that the html_files field in IndependentTestUploadResponse correctly lists all HTML files packaged in the ZIP.
    """
    response = IndependentTestUploadResponse(
        message="Refinement complete",
        conditions_without_matching_configs=[],
        refined_conditions_found=2,
        refined_conditions=[],
        unrefined_eicr="<xml>...</xml>",
        refined_download_url="/api/download/uuid_refined_ecr.zip",
        html_files=["ConditionA-123.html", "ConditionB-456.html"],
    )
    assert hasattr(response, "html_files")
    assert isinstance(response.html_files, list)
    assert "ConditionA-123.html" in response.html_files
    assert "ConditionB-456.html" in response.html_files

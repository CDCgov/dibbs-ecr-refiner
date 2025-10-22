import zipfile

import pytest

from .file_io import create_refined_ecr_zip_in_memory


@pytest.mark.integration
def test_zip_contains_only_xml_when_html_fails() -> None:
    """
    Integration test: ZIP contains only XML if HTML transformation fails for a condition.

    Simulate by omitting HTML file for ConditionC and including for ConditionD.
    """
    files: list[tuple[str, str | bytes]] = [
        ("ConditionC-321.xml", "<xml>TestC</xml>"),  # HTML intentionally omitted for C
        ("ConditionD-654.xml", "<xml>TestD</xml>"),
        ("ConditionD-654.html", b"<html><body>HTML D</body></html>"),
    ]
    zip_name, zip_buf = create_refined_ecr_zip_in_memory(files=files)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        namelist = zf.namelist()
        assert "ConditionC-321.xml" in namelist
        assert "ConditionD-654.xml" in namelist
        assert "ConditionD-654.html" in namelist
        assert "ConditionC-321.html" not in namelist  # HTML missing for C, correct
        # Verify contents
        assert zf.read("ConditionD-654.html").startswith(b"<html")
        assert zf.read("ConditionC-321.xml").decode("utf-8").startswith("<xml>")

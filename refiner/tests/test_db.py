from unittest.mock import patch

import pytest

from app.services.db import get_value_sets_for_condition


@pytest.fixture
def mock_db():
    with patch("sqlite3.connect", autospec=True) as mock_connect:
        mock_conn = mock_connect.return_value
        mock_conn.__enter__.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        yield mock_cursor


def test_get_value_sets_for_condition(mock_db):
    mocked_db_response = [
        ("dxtc", "A36.3|A36", "http://hl7.org/fhir/sid/icd-10-cm", "0363|0036"),
        ("sdtc", "772150003", "http://snomed.info/sct", None),
    ]
    mock_db.fetchall.return_value = mocked_db_response
    returned_dict = get_value_sets_for_condition("276197005")
    expected_result = {
        "dxtc": [
            {"codes": ["A36.3", "A36"], "system": "http://hl7.org/fhir/sid/icd-10-cm"},
            {"codes": ["0363", "0036"], "system": "http://hl7.org/fhir/sid/icd-9-cm"},
        ],
        "sdtc": [{"codes": ["772150003"], "system": "http://snomed.info/sct"}],
    }
    assert returned_dict == expected_result

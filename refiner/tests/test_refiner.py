import pathlib
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from app.main import app

client = TestClient(app)


def parse_file_from_test_assets(filename: str) -> etree.ElementTree:
    """
    Parses a file from the assets directory into an ElementTree.

    :param filename: The name of the file to read.
    :return: An ElementTree containing the contents of the file.
    """
    with open(
        pathlib.Path(__file__).parent.parent / "tests" / "assets" / filename
    ) as file:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file, parser)
        return tree


def read_file_from_test_assets(filename: str) -> str:
    """
    Reads a file from the assets directory.

    :param filename: The name of the file to read.
    :return: A string containing the contents of the file.
    """
    with open(
        (pathlib.Path(__file__).parent.parent / "tests" / "assets" / filename),
    ) as file:
        return file.read()


test_eICR_xml = read_file_from_test_assets("message_refiner_test_eicr.xml")

refined_test_no_parameters = parse_file_from_test_assets(
    "refined_message_no_parameters.xml"
)

refined_test_eICR_social_history_only = parse_file_from_test_assets(
    "refined_message_social_history_only.xml"
)

refined_test_eICR_labs_reason = parse_file_from_test_assets(
    "refined_message_labs_reason.xml"
)

refined_test_condition_only = parse_file_from_test_assets(
    "refined_message_condition_only.xml"
)

refined_test_results_chlamydia_condition = parse_file_from_test_assets(
    "refined_message_results_section_chlamydia_condition.xml"
)

mock_tcr_response = {"lrtc": [{"codes": ["53926-2"], "system": "http://loinc.org"}]}


def test_health_check():
    actual_response = client.get("/")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_openapi():
    actual_response = client.get("/message-refiner/openapi.json")
    assert actual_response.status_code == 200


def test_ecr_refiner():
    # Test case: sections_to_include = None
    expected_response = refined_test_no_parameters
    content = test_eICR_xml
    sections_to_include = None
    endpoint = "/ecr/"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200

    actual_flattened = [i.tag for i in etree.fromstring(actual_response.content).iter()]
    expected_flattened = [i.tag for i in expected_response.iter()]
    assert actual_flattened == expected_flattened

    # Test case: sections_to_include = "29762-2" # social history narrative
    expected_response = refined_test_eICR_social_history_only
    content = test_eICR_xml
    sections_to_include = "29762-2"
    endpoint = f"/ecr/?sections_to_include={sections_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200

    actual_flattened = [i.tag for i in etree.fromstring(actual_response.content).iter()]
    expected_flattened = [i.tag for i in expected_response.iter()]
    assert actual_flattened == expected_flattened

    # Test case: sections_to_include = "30954-2,29299-5" # labs/diagnostics and reason for visit
    expected_response = refined_test_eICR_labs_reason
    content = test_eICR_xml
    sections_to_include = "30954-2,29299-5"
    endpoint = f"/ecr/?sections_to_include={sections_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200
    actual_flattened = [i.tag for i in etree.fromstring(actual_response.content).iter()]
    expected_flattened = [i.tag for i in expected_response.iter()]
    assert actual_flattened == expected_flattened

    # Test case: sections_to_include is invalid
    expected_response = "Invalid section provided."
    content = test_eICR_xml
    sections_to_include = "blah blah blah"
    endpoint = f"/ecr/?sections_to_include={sections_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 422
    assert actual_response.content.decode() == expected_response

    # Test case: raw_message is invalid XML
    content = "invalid XML"
    sections_to_include = None
    endpoint = "/ecr/"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 400
    assert "Invalid XML format." in actual_response.content.decode()


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_ecr_refiner_conditions(mock_get):
    # Mock the response from the trigger-code-reference service
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_tcr_response
    mock_get.return_value = mock_response

    # Test chlamydia condition only
    expected_response = refined_test_condition_only
    content = test_eICR_xml
    conditions_to_include = "240589008"
    endpoint = f"/ecr/?conditions_to_include={conditions_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200

    actual_flattened = [
        i.tag
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element)
    ]
    expected_flattened = [
        i.tag for i in expected_response.iter() if isinstance(i, etree._Element)
    ]
    assert actual_flattened == expected_flattened

    actual_elements = [
        i.tag.split("}")[-1]
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element) and isinstance(i.tag, str)
    ]
    assert "ClinicalDocument" in actual_elements

    # Test results section with chlamydia condition
    expected_response = refined_test_results_chlamydia_condition
    content = test_eICR_xml
    conditions_to_include = "240589008"
    sections_to_include = "30954-2"
    endpoint = f"/ecr/?sections_to_include={sections_to_include}&conditions_to_include={conditions_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200

    actual_flattened = [
        i.tag
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element)
    ]
    expected_flattened = [
        i.tag for i in expected_response.iter() if isinstance(i, etree._Element)
    ]
    assert actual_flattened == expected_flattened

    actual_elements = [
        i.tag.split("}")[-1]
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element) and isinstance(i.tag, str)
    ]
    assert "ClinicalDocument" in actual_elements

    # Test conditions, history of hospitalization section without relevant data
    # this will process in the same way as if no parameters were passed
    expected_response = refined_test_no_parameters
    content = test_eICR_xml
    conditions_to_include = "240589008"
    sections_to_include = "46240-8"
    endpoint = f"/ecr/?sections_to_include={sections_to_include}&conditions_to_include={conditions_to_include}"
    actual_response = client.post(endpoint, content=content)
    assert actual_response.status_code == 200

    actual_flattened = [
        i.tag
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element)
    ]
    expected_flattened = [
        i.tag for i in expected_response.iter() if isinstance(i, etree._Element)
    ]
    assert actual_flattened == expected_flattened

    actual_elements = [
        i.tag.split("}")[-1]
        for i in etree.fromstring(actual_response.content.decode()).iter()
        if isinstance(i, etree._Element) and isinstance(i.tag, str)
    ]
    assert "ClinicalDocument" in actual_elements

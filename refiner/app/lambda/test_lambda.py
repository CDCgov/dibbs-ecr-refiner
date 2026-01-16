import json
from pathlib import Path
from zipfile import ZipFile

import boto3
import pytest
from moto import mock_aws

from ..services.file_io import get_asset_path


@pytest.fixture
def aws_mock():
    with mock_aws():
        yield


@pytest.fixture
def config_bucket_env(monkeypatch) -> str:
    bucket_name = "config-bucket"
    monkeypatch.setenv("S3_BUCKET_CONFIG", bucket_name)
    return bucket_name


@pytest.fixture
def lambda_event() -> dict:
    event_file_path = Path(__file__).parent / "example-events" / "event.json"
    with open(event_file_path) as f:
        return json.load(f)


@pytest.fixture
def sample_xml_files() -> dict[str, bytes]:
    zip_path = get_asset_path("demo", "mon-mothma-covid-influenza.zip")

    with ZipFile(zip_path) as z:
        with z.open("CDA_RR.xml") as f:
            rr_xml = f.read()
        with z.open("CDA_eICR.xml") as f:
            eicr_xml = f.read()

    return {
        "rr_xml": rr_xml,
        "eicr_xml": eicr_xml,
    }


@pytest.fixture
def s3_client(aws_mock):
    return boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def data_bucket(s3_client) -> str:
    bucket_name = "dibbs-refiner-dev"
    s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def config_bucket(s3_client, config_bucket_env) -> str:
    s3_client.create_bucket(Bucket=config_bucket_env)
    return config_bucket_env


@pytest.fixture
def s3_input_objects(
    s3_client,
    data_bucket,
    sample_xml_files,
):
    persistence_id = "persistence/id"

    s3_client.put_object(
        Bucket=data_bucket,
        Key=f"RefinerInput/{persistence_id}",
        Body=sample_xml_files["rr_xml"],
    )

    s3_client.put_object(
        Bucket=data_bucket,
        Key=f"eCRMessageV2/{persistence_id}",
        Body=sample_xml_files["eicr_xml"],
    )

    return persistence_id


def collect_lambda_output_keys(s3_client, bucket) -> list[str]:
    return [obj["Key"] for obj in s3_client.list_objects_v2(Bucket=bucket)["Contents"]]


def get_refiner_complete_content(s3_client, bucket, persistance_id) -> dict:
    resp = s3_client.get_object(Bucket=bucket, Key=f"RefinerComplete/{persistance_id}")
    return json.loads(resp["Body"].read().decode("utf-8"))


@mock_aws
def test_lambda_inactive(
    lambda_event,
    s3_client,
    data_bucket,
    config_bucket,
    s3_input_objects,
):
    """
    Test that a file with two reportable conditions works when configurations are not
    present for either condition.
    """
    from .lambda_function import lambda_handler

    # Run the Lambda
    response = lambda_handler(lambda_event, context={})
    assert response["statusCode"] == 200

    # Collect names of all keys that exist after running the lambda
    created_files = collect_lambda_output_keys(s3_client=s3_client, bucket=data_bucket)

    # Expected input files paths
    assert "RefinerInput/persistence/id" in created_files
    assert "eCRMessageV2/persistence/id" in created_files

    # Expected eICR output files created by Refiner
    full_flu_path = "RefinerOutput/persistence/id/SDDH/772828001/refined_eICR.xml"
    full_covid_path = "RefinerOutput/persistence/id/SDDH/840539006/refined_eICR.xml"

    # Skipped due to no current.json files found
    assert full_flu_path not in created_files
    assert full_covid_path not in created_files

    # Expected completion file for pipeline
    assert "RefinerComplete/persistence/id" in created_files

    # Load RefinerComplete/persistence/id and ensure it contains expected paths
    resp = s3_client.get_object(
        Bucket=data_bucket, Key=f"RefinerComplete/{s3_input_objects}"
    )
    complete_json = json.loads(resp["Body"].read().decode("utf-8"))
    assert not complete_json["RefinerSkip"]

    # Skipped due to no current.json files found
    assert full_flu_path not in complete_json["RefinerOutputFiles"]
    assert full_covid_path not in complete_json["RefinerOutputFiles"]


@mock_aws
def test_lambda_one_current_file(
    lambda_event,
    s3_client,
    data_bucket,
    config_bucket,
    s3_input_objects,
):
    """
    Test that a file with two reportable conditions works when a configuration is
    active for only one of those conditions.
    """
    from .lambda_function import lambda_handler

    # COVID = 840539006
    # Flu = 772828001

    # Create current.json for COVID
    covid_current = {"version": 1}
    s3_client.put_object(
        Bucket=config_bucket,
        Key="SDDH/840539006/current.json",
        Body=json.dumps(covid_current, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    # Create activation for COVID
    covid_activation = {"codes": ["101289-7"], "sections": []}
    s3_client.put_object(
        Bucket=config_bucket,
        Key=f"SDDH/840539006/{covid_current['version']}/active.json",
        Body=json.dumps(covid_activation, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    # Run the Lambda
    response = lambda_handler(lambda_event, context={})
    assert response["statusCode"] == 200

    # Check that expected output files were written
    created_files = collect_lambda_output_keys(s3_client=s3_client, bucket=data_bucket)
    assert f"RefinerComplete/{s3_input_objects}" in created_files
    assert (
        f"RefinerOutput/{s3_input_objects}/SDDH/840539006/refined_eICR.xml"
        in created_files
    )
    assert (
        f"RefinerOutput/{s3_input_objects}/SDDH/840539006/refined_RR.xml"
        in created_files
    )

    # Check that content of RefinerComplete looks correct
    complete_json = get_refiner_complete_content(
        s3_client=s3_client, bucket=data_bucket, persistance_id=s3_input_objects
    )
    assert not complete_json["RefinerSkip"]
    assert (
        f"RefinerOutput/{s3_input_objects}/SDDH/840539006/refined_eICR.xml"
        in complete_json["RefinerOutputFiles"]
    )
    assert (
        f"RefinerOutput/{s3_input_objects}/SDDH/840539006/refined_RR.xml"
        in complete_json["RefinerOutputFiles"]
    )
    assert (
        "RefinerOutput/{s3_input_objects}/SDDH/772828001"
        not in complete_json["RefinerOutputFiles"]
    )

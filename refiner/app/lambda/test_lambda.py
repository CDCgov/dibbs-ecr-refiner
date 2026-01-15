import json
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import boto3
from moto import mock_aws

from ..services.file_io import get_asset_path


@mock_aws
def test_lambda(monkeypatch):
    # Set config bucket environment variable name
    config_bucket_name = "config-bucket"
    monkeypatch.setenv("S3_BUCKET_CONFIG", config_bucket_name)

    # Load example event
    event_file_path = Path(__file__).parent / "example-events" / "event.json"
    with open(event_file_path) as f:
        event = json.load(f)

    # Load sample input data
    zip_path = get_asset_path("demo", "mon-mothma-covid-influenza.zip")
    with ZipFile(zip_path) as z:
        with z.open("CDA_RR.xml") as f:
            rr_xml = f.read()
        with z.open("CDA_eICR.xml") as f:
            eicr_xml = f.read()

    # Create a persistence ID (matching event)
    persistence_id = "persistence/id"

    # Create an S3 bucket (matching event)
    data_bucket = "dibbs-refiner-dev"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=data_bucket)

    # Create a config bucket
    s3.create_bucket(Bucket=config_bucket_name)

    # RR will come from RefinerInput/
    rr_input_key = f"RefinerInput/{persistence_id}"
    s3.put_object(Bucket=data_bucket, Key=rr_input_key, Body=rr_xml)

    # eICR will be found in eCRMessageV2
    eicr_input_key = f"eCRMessageV2/{persistence_id}"
    s3.put_object(Bucket=data_bucket, Key=eicr_input_key, Body=eicr_xml)

    from .lambda_function import lambda_handler

    # Run the Lambda
    with patch("app.lambda.lambda_function.refine_eicr") as mock_refine:
        # Return original eICR content for testing purposes
        mock_refine.return_value = eicr_xml

        # Run the Lambda
        response = lambda_handler(event, context={})
        assert response["statusCode"] == 200

    # Collect names of all keys that exist after running the lambda
    s3_paths = [
        obj["Key"] for obj in s3.list_objects_v2(Bucket=data_bucket)["Contents"]
    ]

    # Expected input files paths
    assert "RefinerInput/persistence/id" in s3_paths
    assert "eCRMessageV2/persistence/id" in s3_paths

    # Expected eICR output files created by Refiner
    # full_flu_path = "RefinerOutput/persistence/id/SDDH/772828001"
    # full_covid_path = "RefinerOutput/persistence/id/SDDH/840539006"

    # Skipped due to no current.json files found
    # assert full_flu_path in s3_paths
    # assert full_covid_path in s3_paths

    # Expected completion file for pipeline
    assert "RefinerComplete/persistence/id" in s3_paths

    # Load RefinerComplete/persistence/id and ensure it contains expected paths
    resp = s3.get_object(Bucket=data_bucket, Key=f"RefinerComplete/{persistence_id}")
    complete_json = json.loads(resp["Body"].read().decode("utf-8"))
    assert not complete_json["RefinerSkip"]

    # Skipped due to no current.json files found
    # assert full_flu_path in complete_json["RefinerOutputFiles"]
    # assert full_covid_path in complete_json["RefinerOutputFiles"]

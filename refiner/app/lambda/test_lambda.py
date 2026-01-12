import json
from pathlib import Path

import boto3
from moto import mock_aws

from .lambda_function import lambda_handler


@mock_aws
def test_lambda():
    # Load example event
    event_file_path = Path(__file__).parent / "example-events" / "event.json"
    with open(event_file_path) as f:
        event = json.load(f)

    # Load sample input data
    rr_file_path = Path(__file__).parent / "test" / "CDA_RR.xml"
    with open(rr_file_path, encoding="utf-8") as f:
        rr_xml = f.read()
    eicr_file_path = Path(__file__).parent / "test" / "CDA_eICR.xml"
    with open(eicr_file_path, encoding="utf-8") as f:
        eicr_xml = f.read()

    # Create a persistence ID (matching event)
    persistence_id = "persistence/id"

    # Create an S3 bucket (matching event)
    bucket = "dibbs-refiner-dev"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket)

    # RR will come from RefinerInput/
    rr_input_key = f"RefinerInput/{persistence_id}"
    s3.put_object(Bucket=bucket, Key=rr_input_key, Body=rr_xml)

    # eICR will be found in eCRMessageV2
    eicr_input_key = f"eCRMessageV2/{persistence_id}"
    s3.put_object(Bucket=bucket, Key=eicr_input_key, Body=eicr_xml)

    # Run the Lambda
    response = lambda_handler(event, context={})
    assert response["statusCode"] == 200

    # Collect names of all keys that exist after running the lambda
    s3_paths = [obj["Key"] for obj in s3.list_objects_v2(Bucket=bucket)["Contents"]]

    # Expected input files paths
    assert "RefinerInput/persistence/id" in s3_paths
    assert "eCRMessageV2/persistence/id" in s3_paths

    # Expected eICR output files created by Refiner
    assert "RefinerOutput/persistence/id/SDDH/772828001" in s3_paths
    assert "RefinerOutput/persistence/id/SDDH/840539006" in s3_paths

    # Expected completion file for pipeline
    assert "RefinerComplete/persistence/id" in s3_paths

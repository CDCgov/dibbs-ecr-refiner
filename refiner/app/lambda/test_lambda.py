import base64
import json
from pathlib import Path

import boto3
from moto import mock_aws

from .lambda_function import lambda_handler


@mock_aws
def test_lambda():
    event_file_path = Path(__file__).parent / "example-events" / "event.json"
    with open(event_file_path) as f:
        event = json.load(f)

    bucket = "dibbs-refiner-dev"

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket)

    # Define sample input file test data
    test_data = {
        "eicr": base64.b64encode(b"<eicr>test</eicr>").decode("utf-8"),
        "rr": base64.b64encode(b"<rr>test</rr>").decode("utf-8"),
    }

    # Convert dict to JSON string and encode as bytes
    json_str = json.dumps(test_data)
    json_bytes = json_str.encode("utf-8")

    input_key = "RefinerInput/testfile"
    s3.put_object(Bucket=bucket, Key=input_key, Body=json_bytes)

    response = lambda_handler(event, context={})
    assert response["statusCode"] == 200

    # Collect names of all keys that exist after running the lambda
    output_objects = s3.list_objects_v2(Bucket=bucket)
    result = {"RefinerInput": 0, "RefinerOutput": 0, "RefinerComplete": 0}
    for obj in output_objects["Contents"]:
        input_key = obj["Key"]
        key_prefix, _, _ = input_key.partition("/")
        result[key_prefix] = result[key_prefix] + 1

    # Provided 1 input file
    assert result["RefinerInput"] == 1

    # Lambda uses 2 mock eICRs
    assert result["RefinerOutput"] == 2

    # 1 resulting "complete" file
    assert result["RefinerComplete"] == 1

# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import logging

import boto3
import json
import os
import base64
import datetime
import uuid

# Initialize the logger
logger = logging.getLogger()
logger.setLevel("INFO")

input_prefix = os.environ.get("REFINER_INPUT_PREFIX") or "RefinerInput"
output_prefix = os.environ.get("REFINER_OUTPUT_PREFIX") or "RefinerOutput"
complete_prefix = os.environ.get("REFINER_COMPLETE_PREFIX") or "RefinerComplete"


def lambda_handler(event, context):
    """
    Main Lambda handler function.

    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        logger.info(f"Event: {event}")
        # Parse the input event
        parsed_event = json.loads(event["Records"])

        # Iterate over the records and parse the S3 event
        for record in parsed_event["Records"]:
            logger.info(f"Record: {record}")

            # Initialize the S3 client
            region = record["awsRegion"]
            s3_client = boto3.client('s3', region_name=region)

            # Parse the S3 event
            s3_event = json.loads(record["body"])
            s3_object_key = s3_event["detail"]["object"]["key"]
            s3_bucket_name = s3_event["detail"]["bucket"]["name"]

            logger.info(f"Processing S3 Object: s3://{s3_bucket_name}/{s3_object_key}")

            # Get the file from S3
            response = s3_client.get_object(
                Bucket=s3_bucket_name,
                Key=s3_object_key
            )
            file_content = response['Body'].read()

            # I forgot our thought on the content of this object, I will assume this format:
            # {"eicr": <base64 encoded string>, "rr": <base64 encoded string>}

            # Decode the base64 encoded strings
            data = json.loads(file_content)
            eicr = base64.b64decode(data["eicr"]).decode("utf-8")
            rr = base64.b64decode(data["rr"]).decode("utf-8")

            # Process the EICR and RR using the refiner
            output_files = refiner_library.refine(eicr, rr)

            output_s3_paths = []
            # Upload the output files to S3
            for output_file in output_files:
                # Generate unique output prefix using timestamp and UUID
                timestamp = datetime.datetime.now().strftime("%Y/%m/%d")
                unique_id = str(uuid.uuid4())
                output_key = f"{timestamp}/{unique_id}"
                s3_client.put_object(
                    Bucket=s3_bucket_name,
                    Key=f"{output_prefix}/{output_key}",
                    Body=output_file
                )
                output_s3_paths.append(f"{output_prefix}/{output_key}")

            # Update the S3 object with the output paths
            # Use the original s3_object_key with the complete prefix
            complete_key = s3_object_key.replace(input_prefix, complete_prefix)
            s3_client.put_object(
                Bucket=s3_bucket_name,
                Key=complete_key,
                Body=json.dumps(output_s3_paths)
            )

        return {"statusCode": 200, "message": "Refiner processed successfully"}

    except Exception as e:
        logger.error(f"Error processing: {str(e)}")
        raise

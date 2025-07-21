# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import base64
import datetime
import json
import logging
import os
import uuid

import boto3

from ..core.models.types import XMLFiles
from ..services.refine import build_condition_eicr_pairs, process_rr, refine_eicr

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
            s3_client = boto3.client("s3", region_name=region)

            # Parse the S3 event
            s3_event = json.loads(record["body"])
            s3_object_key = s3_event["detail"]["object"]["key"]
            s3_bucket_name = s3_event["detail"]["bucket"]["name"]

            logger.info(f"Processing S3 Object: s3://{s3_bucket_name}/{s3_object_key}")

            # Get the file from S3
            response = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_object_key)
            file_content = response["Body"].read()

            # I forgot our thought on the content of this object, I will assume this format:
            # {"eicr": <base64 encoded string>, "rr": <base64 encoded string>}

            # Decode the base64 encoded strings
            data = json.loads(file_content)
            eicr = base64.b64decode(data["eicr"]).decode("utf-8")
            rr = base64.b64decode(data["rr"]).decode("utf-8")

            # Process the EICR and RR using the refiner
            # NOTE: Need a database for this to work
            # refined_eicr_docs = run_refinement_process(eicr=eicr, rr=rr)

            # Sample data until we have database connectivity
            refined_eicr_docs = [
                f"<doc><eicr>{eicr}</eicr></doc>",
                f"<doc><rr>{rr}</rr></doc>",
            ]
            logger.info("Sample data:", refined_eicr_docs)

            output_s3_paths = []
            # Upload the output files to S3
            for refined_eicr_doc in refined_eicr_docs:
                # Generate unique output prefix using timestamp and UUID
                timestamp = datetime.datetime.now().strftime("%Y/%m/%d")
                unique_id = str(uuid.uuid4())
                output_key = f"{timestamp}/{unique_id}"

                s3_client.put_object(
                    Bucket=s3_bucket_name,
                    Key=f"{output_prefix}/{output_key}",
                    Body=refined_eicr_doc.encode("utf-8"),
                    ContentType="application/xml",
                )
                output_s3_paths.append(f"{output_prefix}/{output_key}")

            # Update the S3 object with the output paths
            # Use the original s3_object_key with the complete prefix
            complete_key = s3_object_key.replace(input_prefix, complete_prefix)
            s3_client.put_object(
                Bucket=s3_bucket_name,
                Key=complete_key,
                Body=json.dumps(output_s3_paths),
            )

        return {"statusCode": 200, "message": "Refiner processed successfully"}

    except Exception as e:
        logger.error(f"Error processing: {str(e)}")
        raise


def run_refinement_process(eicr: str, rr: str) -> list[str]:
    """
    Process the RR for reportable conditions, create XML file pairs per condition,
    and run the refiner against all files. Returns a list of refined eICR XML strings.

    Args:
        eicr (str): The eICR as an XML string
        rr (str): The RR as an XML string

    Returns:
        list[str]: XML for each refined eICR
    """
    # Create XMLFiles from pair
    original_xml_files = XMLFiles(eicr=eicr, rr=rr)

    # Process the RR to get reportable conditions
    rr_results = process_rr(original_xml_files)
    reportable_conditions = rr_results["reportable_conditions"]

    # create condition-eICR pairs with XMLFiles objects
    condition_eicr_pairs = build_condition_eicr_pairs(
        original_xml_files, reportable_conditions
    )

    # Create separate XML file pairs per condition and run the refinement process
    refined_eicr_docs = []
    for pair in condition_eicr_pairs:
        condition = pair["reportable_condition"]
        xml_files = pair[
            "xml_files"
        ]  # Each pair contains a distinct XMLFiles instance.

        # refine the eICR for this specific condition code.
        refined_eicr = refine_eicr(
            xml_files=xml_files,
            condition_codes=condition["code"],
        )

        # Add refined eICR XML doc to the list
        refined_eicr_docs.append(refined_eicr)

    return refined_eicr_docs

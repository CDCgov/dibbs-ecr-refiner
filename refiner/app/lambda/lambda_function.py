# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import json
import logging
import os
from typing import Any, TypedDict

import boto3
from botocore.exceptions import ClientError

from ..core.models.types import XMLFiles
from ..services.ecr.refine import (
    create_eicr_refinement_plan,
    create_rr_refinement_plan,
    refine_eicr,
    refine_rr,
)
from ..services.ecr.reportability import determine_reportability
from ..services.terminology import ProcessedConfiguration

# Initialize the logger
logger = logging.getLogger()
logger.setLevel("INFO")

# Environment variables
EICR_INPUT_PREFIX = os.getenv("EICR_INPUT_PREFIX", "eCRMessageV2/")
REFINER_INPUT_PREFIX = os.getenv("REFINER_INPUT_PREFIX", "RefinerInput/")
REFINER_OUTPUT_PREFIX = os.getenv("REFINER_OUTPUT_PREFIX", "RefinerOutput/")
REFINER_COMPLETE_PREFIX = os.getenv("REFINER_COMPLETE_PREFIX", "RefinerComplete/")
S3_BUCKET_CONFIG = os.getenv("S3_BUCKET_CONFIG")


class RefinerCompleteFile(TypedDict):
    """
    Represents the completion file written after all refinement is done.
    """

    RefinerSkip: bool
    RefinerOutputFiles: list[str]


def extract_persistence_id(object_key: str, input_prefix: str) -> str:
    """
    Extract the persistence_id from an S3 object key.

    Object key format: <pipeline-step>/<persistance_id>
    Example: RefinerInput/2026/01/01/0026b704-f510-4494-8d21-11d27217d96e
    Returns: 2026/01/01/0026b704-f510-4494-8d21-11d27217d96e

    Args:
        object_key: The S3 object key
        input_prefix: The pipeline step prefix (e.g., "RefinerInput/")

    Returns:
        str: The persistence_id portion of the key
    """
    if not object_key.startswith(input_prefix):
        raise ValueError(
            f"Object key '{object_key}' does not start with expected prefix '{input_prefix}'"
        )
    return object_key[len(input_prefix) :]


def get_s3_object_content(s3_client, bucket: str, key: str) -> str:
    """
    Retrieve and decode an S3 object as UTF-8 string.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        str: The object content as a UTF-8 string
    """
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


def _s3_object_exists(s3_client, bucket: str, key: str) -> bool:
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code in ("404", "NoSuchKey"):
            return False

        logger.error("Unexpected error while fetching file from S3: ${key}", e)
        raise


def s3_content_to_dict(body: Any) -> dict:
    try:
        data = json.loads(body)
        return data
    except json.JSONDecodeError:
        raise


def read_current_version(s3_client, bucket: str, key: str) -> int | None:
    """
    Fetches the current active configuration version from `current.json` in the
    configuration bucket if one exists. If the version is `null` or the file does not exist,
    returns None;

    Returns:
        str | None: Active configuration version as an int, or None if no active version exists
    """

    # Check `current.json` file existance, return None if no object exists
    current_exists = _s3_object_exists(s3_client=s3_client, bucket=bucket, key=key)

    if not current_exists:
        return None

    # Read the file content and ensure required data is present
    current_version_content = get_s3_object_content(s3_client, bucket=bucket, key=key)

    current_version_dict = s3_content_to_dict(current_version_content)

    # Check version existance and ensure it's an int
    if isinstance(current_version_dict.get("version"), int):
        return int(current_version_dict["version"])

    return None


def read_configuration_file(s3_client, bucket: str, key: str) -> dict:
    # Check that configuration file exists
    config_exists = _s3_object_exists(s3_client=s3_client, bucket=bucket, key=key)

    if not config_exists:
        # It should exist because we've already checked the active version by this point
        raise Exception(f"Activated configuration file could not be read at: {key}")

    # Read the file content and ensure required data is present
    config_file_content = get_s3_object_content(s3_client, bucket=bucket, key=key)

    return s3_content_to_dict(config_file_content)


def process_refiner(
    xml_files: XMLFiles, s3_client, bucket: str, config_bucket: str, persistence_id: str
) -> list[str]:
    """
    Process eICR and RR through the refiner for all jurisdictions and conditions.

    This function:
    1. Extracts all reportable conditions grouped by jurisdiction from the RR
    2. For each jurisdiction/condition combination, processes the refinement
    3. Returns a list of S3 paths for the refined output files

    Args:
        xml_files: Container with eICR and RR XML strings
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        persistence_id: The persistence ID for constructing output paths

    Returns:
        list[str]: List of S3 paths for refined output files
    """
    # Extract reportable conditions by jurisdiction from RR
    reportability_result = determine_reportability(xml_files)
    refiner_output_files: list[str] = []

    # Process each jurisdiction
    for jurisdiction_group in reportability_result["reportable_conditions"]:
        jurisdiction_code = jurisdiction_group.jurisdiction.upper()

        # Process each condition for this jurisdiction
        for condition in jurisdiction_group.conditions:
            condition_code = condition.code

            # TODO: Implement actual refinement logic
            # This requires:
            # 1. Reading configuration from S3
            # 2. Mapping RC SNOMED codes to conditions
            # 3. Building ProcessedConfiguration
            # 4. Calling refine_eicr()
            #
            # For now, we'll create a placeholder structure
            # The actual refinement will be implemented when configurations are available from S3

            current_file_key = f"{jurisdiction_code}/{condition_code}/current.json"
            config_version_to_use = read_current_version(
                s3_client=s3_client,
                bucket=config_bucket,
                key=current_file_key,
            )

            # Skip if no active configuration for the condition is in use
            if not config_version_to_use:
                logger.info(
                    f"No active configuration identified at key={current_file_key} while processing jurisdiction={jurisdiction_code}, condition={condition_code}, skipping"
                )
                continue

            logger.info(
                f"Current file found key={current_file_key} version={config_version_to_use}"
            )

            logger.info(
                f"Processing jurisdiction={jurisdiction_code}, condition={condition_code}"
            )

            # Construct output path: RefinerOutput/<persistance_id>/<jurisdiction_code>/<condition_code>
            output_key = f"{REFINER_OUTPUT_PREFIX}{persistence_id}/{jurisdiction_code}/{condition_code}"

            # TODO: Replace with actual refined eICR content
            # For now, using original eICR as placeholder

            # Read active configuration
            # /jurisdiction_code/condition_code/version/active.json
            serialized_configuration_key = f"{jurisdiction_code}/{condition_code}/{config_version_to_use}/active.json"
            serialized_configuration = read_configuration_file(
                s3_client=s3_client,
                bucket=config_bucket,
                key=serialized_configuration_key,
            )

            logger.info(
                f"Using activated configuration file key={serialized_configuration_key}"
            )

            processed_configuration = ProcessedConfiguration.from_dict(
                serialized_configuration
            )

            eicr_refinement_plan = create_eicr_refinement_plan(
                xml_files=xml_files, processed_configuration=processed_configuration
            )

            # Run refinement
            refined_eicr_content = refine_eicr(
                xml_files=xml_files, plan=eicr_refinement_plan
            )

            # Run RR refinement
            rr_refinement_plan = create_rr_refinement_plan(
                processed_configuration=processed_configuration
            )

            refined_rr_content = refine_rr(
                xml_files=xml_files,
                jurisdiction_id=jurisdiction_code,
                plan=rr_refinement_plan,
            )

            # Upload refined eICR and RR to S3
            eicr_output_key = f"{output_key}/refined_eICR.xml"
            s3_client.put_object(
                Bucket=bucket,
                Key=eicr_output_key,
                Body=refined_eicr_content.encode("utf-8"),
                ContentType="application/xml",
            )
            refiner_output_files.append(eicr_output_key)
            logger.info(f"Created refined output: {eicr_output_key}")

            rr_output_key = f"{output_key}/refined_RR.xml"
            s3_client.put_object(
                Bucket=bucket,
                Key=rr_output_key,
                Body=refined_rr_content.encode("utf-8"),
                ContentType="application/xml",
            )
            refiner_output_files.append(rr_output_key)
            logger.info(f"Created refined output: {rr_output_key}")

    return refiner_output_files


def lambda_handler(event, context):
    """
    Main Lambda handler function.

    Processes S3 events from SQS to refine eICR documents.

    Event structure:
    - Records: List of SQS records
    - Each record.body contains an EventBridge S3 event JSON string
    - The S3 event detail contains bucket name and object key

    Parameters:
        event: Dict containing the Lambda function event data from SQS
        context: Lambda runtime context

    Returns:
        Dict containing status message
    """
    try:
        logger.info(f"Received event with {len(event.get('Records', []))} record(s)")
        s3_config_bucket_name = S3_BUCKET_CONFIG

        if not s3_config_bucket_name:
            raise Exception("S3_BUCKET_CONFIG environment variable must be defined.")

        # Process each SQS record
        for record in event["Records"]:
            logger.info(f"Processing record: {record.get('messageId')}")

            # Initialize the S3 client
            region = record["awsRegion"]
            s3_client = boto3.client("s3", region_name=region)

            # Parse the EventBridge S3 event from the SQS message body
            s3_event = json.loads(record["body"])
            s3_object_key = s3_event["detail"]["object"]["key"]
            s3_bucket_name = s3_event["detail"]["bucket"]["name"]

            logger.info(f"Processing S3 Object: s3://{s3_bucket_name}/{s3_object_key}")

            # Extract persistence_id from the RR object key
            persistence_id = extract_persistence_id(s3_object_key, REFINER_INPUT_PREFIX)
            logger.info(f"Extracted persistence_id: {persistence_id}")

            # S3 GET RR
            logger.info(f"Retrieving RR from s3://{s3_bucket_name}/{s3_object_key}")
            rr_content = get_s3_object_content(s3_client, s3_bucket_name, s3_object_key)

            # Construct eICR path: s3://<bucket>/<EICR_Input_Prefix>/<persistance_id>
            eicr_key = f"{EICR_INPUT_PREFIX}{persistence_id}"
            logger.info(f"Retrieving eICR from s3://{s3_bucket_name}/{eicr_key}")

            # S3 GET eICR
            eicr_content = get_s3_object_content(s3_client, s3_bucket_name, eicr_key)

            # Create XMLFiles container
            xml_files = XMLFiles(eicr=eicr_content, rr=rr_content)

            # Process Refiner (eICR, RR) -> Refiner Output []
            logger.info("Starting refinement process")
            refiner_output_files = process_refiner(
                xml_files,
                s3_client,
                s3_bucket_name,
                s3_config_bucket_name,
                persistence_id,
            )

            # Create RefinerComplete file
            complete_file: RefinerCompleteFile = {
                "RefinerSkip": False,
                "RefinerOutputFiles": refiner_output_files,
            }

            # Construct RefinerComplete path: RefinerComplete/<persistance_id>
            complete_key = f"{REFINER_COMPLETE_PREFIX}{persistence_id}"

            # PUT RefinerCompleteFile
            logger.info(
                f"Writing completion file to s3://{s3_bucket_name}/{complete_key}"
            )
            s3_client.put_object(
                Bucket=s3_bucket_name,
                Key=complete_key,
                Body=json.dumps(complete_file, indent=2),
                ContentType="application/json",
            )

            logger.info(
                f"Successfully processed {len(refiner_output_files)} refined outputs"
            )

        return {"statusCode": 200, "message": "Refiner processed successfully"}

    except Exception as e:
        logger.error(f"Error processing: {str(e)}", exc_info=True)
        raise

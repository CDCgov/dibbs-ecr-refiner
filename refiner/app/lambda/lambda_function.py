# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import json
import os
from collections import defaultdict
from typing import TypedDict

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from app.core.utils import get_env_variable
from app.db.conditions.model import ConditionMappingPayload

from ..core.models.types import XMLFiles
from ..services.aws.s3_keys import (
    get_active_file_key,
    get_current_file_key,
    get_rsg_cg_mapping_file_key,
)
from ..services.ecr.refine import refine_rr_for_unconfigured_conditions
from ..services.pipeline import (
    RefinementTrace,
    discover_reportable_conditions,
    refine_for_condition,
)
from ..services.terminology import ProcessedConfiguration

# Initialize the logger
logger = Logger(service="refiner")

# Environment variables
EICR_INPUT_PREFIX = get_env_variable("EICR_INPUT_PREFIX")
REFINER_INPUT_PREFIX = get_env_variable("REFINER_INPUT_PREFIX")
REFINER_OUTPUT_PREFIX = get_env_variable("REFINER_OUTPUT_PREFIX")
REFINER_COMPLETE_PREFIX = get_env_variable("REFINER_COMPLETE_PREFIX")
S3_BUCKET_CONFIG = get_env_variable("S3_BUCKET_CONFIG")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # No need to set this in a live env


class RefinerCompleteFile(TypedDict):
    """
    Represents the completion file written after all refinement is done.
    """

    RefinerMetadata: dict[str, dict[str, bool]]
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


def check_s3_object_exists(s3_client, bucket: str, key: str) -> bool:
    """
    Check whether an object exists in S3 using a HEAD request.

    Args:
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        key: S3 object key.

    Returns:
        bool: True if the object exists, False if not found.

    Raises:
        Exception: If the S3 request fails with an error other than 404/NoSuchKey.
    """

    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code in ("404", "NoSuchKey"):
            return False

        raise Exception(f"Unexpected error while fetching file from S3: {key}", e)


def parse_s3_content_to_dict(body: str) -> dict:
    """
    Parse a JSON string into a dictionary.

    Args:
        body: A JSON-encoded string, typically read from an S3 object.

    Returns:
        dict: The parsed dictionary.

    Raises:
        json.JSONDecodeError: If the string is not valid JSON.
    """

    try:
        data = json.loads(body)
        return data
    except json.JSONDecodeError as e:
        logger.error("Decoding S3 string to JSON failed", e)
        raise


def read_rsg_cg_mapping_file(s3_client, bucket: str, key: str) -> dict | None:
    """
    Read the RSG-to-condition-grouper mapping file for a jurisdiction from S3.

    This file maps RSG SNOMED codes to condition grouper metadata (canonical URL,
    name, TES version). Lambda uses it to determine which condition grouper an
    RSG code from the RR belongs to, and where to find the corresponding
    configuration files.

    Args:
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        key: S3 object key for the mapping file.

    Returns:
        dict | None: The mapping data as a dictionary, or None if the file
            does not exist or is empty.
    """

    # Check that mapping file exists
    mapping_exists = check_s3_object_exists(s3_client=s3_client, bucket=bucket, key=key)

    if not mapping_exists:
        return None

    # Read the file content, return it as a dict
    mapping_file_content = get_s3_object_content(s3_client, bucket=bucket, key=key)
    content_dict = parse_s3_content_to_dict(mapping_file_content)
    if not content_dict:
        return None

    return content_dict


def read_current_version(s3_client, bucket: str, key: str) -> int | None:
    """
    Fetches the current active configuration version from `current.json` in the
    configuration bucket if one exists. If the version is `null` or the file does not exist,
    returns None;

    Returns:
        int | None: Active configuration version as an int, or None if no active version exists
    """

    # Check `current.json` file existance, return None if no object exists
    current_exists = check_s3_object_exists(s3_client=s3_client, bucket=bucket, key=key)

    if not current_exists:
        return None

    # Read the file content and ensure required data is present
    current_version_content = get_s3_object_content(s3_client, bucket=bucket, key=key)

    current_version_dict = parse_s3_content_to_dict(current_version_content)

    # Check version existance and ensure it's an int
    if isinstance(current_version_dict.get("version"), int):
        return int(current_version_dict["version"])

    return None


def read_configuration_file(s3_client, bucket: str, key: str) -> dict:
    """
    Read an activated configuration file (active.json) from S3.

    This file contains the serialized configuration data needed for refinement,
    including the flat codes set, per-system code_system_sets, section processing
    rules, and included condition RSG codes. It is written during activation by
    the webapp and read by Lambda at refinement time.

    Args:
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        key: S3 object key for the configuration file.

    Returns:
        dict: The configuration data as a dictionary.

    Raises:
        Exception: If the file does not exist. This indicates a mismatch between
            current.json (which pointed to this version) and the actual files on S3.
    """

    # Check that configuration file exists
    config_exists = check_s3_object_exists(s3_client=s3_client, bucket=bucket, key=key)

    if not config_exists:
        # It should exist because we've already checked the active version by this point
        raise Exception(f"Activated configuration file could not be read at: {key}")

    # Read the file content and ensure required data is present
    config_file_content = get_s3_object_content(
        s3_client=s3_client, bucket=bucket, key=key
    )

    return parse_s3_content_to_dict(config_file_content)


def process_refiner(
    xml_files: XMLFiles,
    s3_client,
    bucket: str,
    config_bucket: str,
    persistence_id: str,
) -> tuple[list[str], dict[str, dict[str, bool]]]:
    """
    Process eICR and RR through the refiner for all jurisdictions and conditions.

    This function:
    1. Uses the shared pipeline to discover reportable conditions from the RR
    2. For each jurisdiction, resolves configurations from S3
    3. For each condition with an active config, uses the shared pipeline to refine
    4. For conditions without active configs, produces unrefined condition RRs
    5. Returns a list of S3 paths for the refined output files and metadata
       indicating which jurisdiction/condition combinations were processed

    Args:
        xml_files: Container with eICR and RR XML strings
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        config_bucket: S3 configuration bucket name
        persistence_id: The persistence ID for constructing output paths

    Returns:
        tuple: A tuple containing:
            - list[str]: List of S3 paths for refined output files
            - dict[str, dict[str, bool]]: Metadata mapping jurisdiction codes
              to condition codes with True (refined) or False (skipped)
    """

    # STAGE 1:
    # use the shared pipeline to discover reportable conditions
    reportable_groups = discover_reportable_conditions(xml_files)
    logger.info(
        "Discovered reportable conditions from RR",
        reportable_group_payload=reportable_groups,
        operation="discovered_reportability",
    )

    refiner_output_files: list[str] = []
    metadata: dict[str, dict[str, bool]] = {}
    non_active_reportable_conditions: dict[str, set[str]] = defaultdict(set)
    all_traces: list[RefinementTrace] = []

    # STAGE 2:
    # resolve configurations from S3 and refine
    for jurisdiction_group in reportable_groups:
        jurisdiction_code = jurisdiction_group.jurisdiction.upper()

        if jurisdiction_code not in metadata:
            metadata[jurisdiction_code] = {}

            # read the RSG → CG mapping file for this jurisdiction
            rsg_cg_mapping_file_key = get_rsg_cg_mapping_file_key(
                jurisdiction_id=jurisdiction_code
            )
            rsg_cg_mapping = read_rsg_cg_mapping_file(
                s3_client=s3_client, bucket=config_bucket, key=rsg_cg_mapping_file_key
            )

            if not rsg_cg_mapping:
                # no mapping file -> skip all conditions for this jurisdiction
                for c in jurisdiction_group.conditions:
                    trace = RefinementTrace(
                        jurisdiction_code=jurisdiction_code,
                        rsg_code=c.code,
                        refinement_outcome="skipped",
                        skip_reason="no_mapping_file",
                    )
                    all_traces.append(trace)
                    non_active_reportable_conditions[jurisdiction_code].add(c.code)
                    metadata[jurisdiction_code][c.code] = False

                logger.info(
                    "Mapping file is empty or does not exist, skipping processing for jurisdiction.",
                    key=rsg_cg_mapping_file_key,
                    jurisdiction_code=jurisdiction_code,
                    operation="skipped",
                )
                continue

            # create the RSG → CG payload
            rsg_cg_payload = ConditionMappingPayload.from_dict(rsg_cg_mapping)

            # process each condition for this jurisdiction
            for rsg_metadata in jurisdiction_group.conditions:
                rsg_code = rsg_metadata.code

                # initialize a trace for this condition
                trace = RefinementTrace(
                    jurisdiction_code=jurisdiction_code,
                    rsg_code=rsg_code,
                )

                if rsg_code not in rsg_cg_payload.mappings.keys():
                    # the RSG isn't in the CG map -> not active
                    trace.refinement_outcome = "skipped"
                    trace.skip_reason = "rsg_not_in_mapping"
                    all_traces.append(trace)

                    metadata[jurisdiction_code][rsg_code] = False
                    non_active_reportable_conditions[jurisdiction_code].add(rsg_code)

                    logger.info(
                        "RSG code isn't in the CG map, skipping.",
                        rsg_code=rsg_code,
                        rsg_cg_payload=rsg_cg_payload.to_dict(),
                        jurisdiction_code=jurisdiction_code,
                        operation="skipped",
                    )
                    continue

                cg_metadata = rsg_cg_payload.mappings[rsg_code]
                trace.condition_grouper_name = cg_metadata.name

                # read current.json to find the active version
                current_file_key = get_current_file_key(
                    jurisdiction_id=jurisdiction_code,
                    canonical_url=cg_metadata.canonical_url,
                )
                config_version_to_use = read_current_version(
                    s3_client=s3_client,
                    bucket=config_bucket,
                    key=current_file_key,
                )
                if not config_version_to_use:
                    trace.refinement_outcome = "skipped"
                    trace.skip_reason = "no_active_configuration"
                    all_traces.append(trace)

                    metadata[jurisdiction_code][rsg_code] = False
                    non_active_reportable_conditions[jurisdiction_code].add(rsg_code)

                    logger.info(
                        "No active configuration identified, skipping.",
                        key=current_file_key,
                        jurisdiction_code=jurisdiction_code,
                        rsg_metadata=rsg_metadata,
                        operation="skipped",
                    )
                    continue

                trace.configuration_version = config_version_to_use

                # read the active configuration file
                serialized_configuration_key = get_active_file_key(
                    jurisdiction_id=jurisdiction_code,
                    canonical_url=cg_metadata.canonical_url,
                    version=config_version_to_use,
                )
                serialized_configuration = read_configuration_file(
                    s3_client=s3_client,
                    bucket=config_bucket,
                    key=serialized_configuration_key,
                )

                logger.info(
                    "Using activated configuration file",
                    key=serialized_configuration_key,
                    jurisdiction_code=jurisdiction_code,
                    canonical_url=cg_metadata.canonical_url,
                    rsg_code=rsg_code,
                    config_version=config_version_to_use,
                    operation="activation_file_read",
                )

                processed_configuration = ProcessedConfiguration.from_dict(
                    serialized_configuration
                )

                # STAGE 3:
                # use the shared pipeline to execute refinement
                result = refine_for_condition(
                    xml_files=xml_files,
                    processed_configuration=processed_configuration,
                    trace=trace,
                )
                all_traces.append(trace)

                # write refined outputs to S3
                output_key = f"{REFINER_OUTPUT_PREFIX}{persistence_id}/{jurisdiction_code}/{cg_metadata.name}"

                eicr_output_key = f"{output_key}/refined_eICR.xml"
                s3_client.put_object(
                    Bucket=bucket,
                    Key=eicr_output_key,
                    Body=result.refined_eicr.encode("utf-8"),
                    ContentType="application/xml",
                )
                refiner_output_files.append(eicr_output_key)

                rr_output_key = f"{output_key}/refined_RR.xml"
                s3_client.put_object(
                    Bucket=bucket,
                    Key=rr_output_key,
                    Body=result.refined_rr.encode("utf-8"),
                    ContentType="application/xml",
                )
                refiner_output_files.append(rr_output_key)

                logger.info(
                    "Condition refinement complete.",
                    eicr_key=eicr_output_key,
                    rr_key=rr_output_key,
                    eicr_size_reduction_percentage=trace.eicr_size_reduction_percentage,
                    jurisdiction_code=jurisdiction_code,
                    condition_code=rsg_code,
                    operation="condition_refinement_complete",
                )

                metadata[jurisdiction_code][rsg_code] = True

    # STAGE 4:
    # create unrefined condition RRs for conditions without active configs
    for jurisdiction_code, condition_codes in non_active_reportable_conditions.items():
        unrefined_rr_content = refine_rr_for_unconfigured_conditions(
            xml_files=xml_files,
            condition_codes=condition_codes,
        )

        output_key = (
            f"{REFINER_OUTPUT_PREFIX}{persistence_id}/{jurisdiction_code}/unrefined_rr"
        )

        rr_output_key = f"{output_key}/refined_RR.xml"
        s3_client.put_object(
            Bucket=bucket,
            Key=rr_output_key,
            Body=unrefined_rr_content.encode("utf-8"),
            ContentType="application/xml",
        )
        refiner_output_files.append(rr_output_key)

        logger.info(
            "Created unrefined conditions RR",
            output_key=rr_output_key,
            jurisdiction_code=jurisdiction_code,
            condition_codes=list(condition_codes),
            operation="unrefined_conditions_rr_written",
        )

    # log summary with all traces
    logger.info(
        "Refinement complete.",
        persistence_id=persistence_id,
        output_file_urls=refiner_output_files,
        traces=[
            {
                "jurisdiction": t.jurisdiction_code,
                "rsg_code": t.rsg_code,
                "condition_grouper": t.condition_grouper_name,
                "outcome": t.refinement_outcome,
                "skip_reason": t.skip_reason,
                "config_version": t.configuration_version,
                "eicr_size_reduction": t.eicr_size_reduction_percentage,
            }
            for t in all_traces
        ],
        operation="refinement_complete",
    )
    return list(set(refiner_output_files)), metadata


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

        # Process each SQS record
        for record in event["Records"]:
            logger.info(f"Processing record: {record.get('messageId')}")

            # Initialize the S3 client
            region = record["awsRegion"]
            s3_client = boto3.client(
                "s3",
                region_name=region,
                endpoint_url=S3_ENDPOINT_URL,
            )

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
            rr_content = get_s3_object_content(
                s3_client=s3_client, bucket=s3_bucket_name, key=s3_object_key
            )
            logger.info("Retrieved RR from s3")

            # Construct eICR path: s3://<bucket>/<EICR_Input_Prefix>/<persistance_id>
            eicr_key = f"{EICR_INPUT_PREFIX}{persistence_id}"
            logger.info(f"Retrieving eICR from s3://{s3_bucket_name}/{eicr_key}")

            # S3 GET eICR
            eicr_content = get_s3_object_content(
                s3_client=s3_client, bucket=s3_bucket_name, key=eicr_key
            )
            logger.info("Retrieved eICR from s3")

            # Create XMLFiles container
            xml_files = XMLFiles(eicr=eicr_content, rr=rr_content)

            # Process Refiner (eICR, RR) -> Refiner Output []
            logger.info("Starting refinement process")
            refiner_output_files, refiner_metadata = process_refiner(
                xml_files,
                s3_client,
                s3_bucket_name,
                s3_config_bucket_name,
                persistence_id,
            )

            # Create RefinerComplete file
            complete_file: RefinerCompleteFile = {
                "RefinerMetadata": refiner_metadata,
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
        logger.error(f"Error processing: {str(e)}", exception=e)
        raise

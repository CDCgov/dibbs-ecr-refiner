# Based on sample code: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-example

# This file uses the default `lambda_function.py` and `lambda_handler` naming conventions. If either
# of these were to change, we'd need to modify this in AWS.
# See here: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html#python-handler-naming

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, TypedDict

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from app.core.utils import get_env_variable
from app.db.conditions.model import ConditionMappingPayload, ConditionMapValue
from app.services.ecr.model import JurisdictionReportableConditions, ReportableCondition

from ..core.models.types import XMLFiles
from ..services.aws.s3_keys import (
    get_active_file_key,
    get_current_file_key,
    get_rsg_cg_mapping_file_key,
)
from ..services.ecr.refine import refine_rr_for_unconfigured_conditions
from ..services.pipeline import (
    RefinementResult,
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

# Type helpers
JurisdictionCode = str
ConditionCode = str
RefinementMetadata = dict[JurisdictionCode, dict[ConditionCode, bool]]


class RefinerCompleteFile(TypedDict):
    """
    Represents the completion file written after all refinement is done.
    """

    RefinerMetadata: RefinementMetadata
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


@dataclass
class RefinementState:
    """
    Mutable state accumulated during refinement processing.
    """

    output_files: list[str] = field(default_factory=list)
    metadata: RefinementMetadata = field(default_factory=dict)
    non_active_reportable_conditions: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    traces: list[RefinementTrace] = field(default_factory=list)


@dataclass
class ProcessRefinerInput:
    xml_files: XMLFiles
    s3_client: Any
    config_bucket_name: str
    output_bucket_name: str
    persistence_id: str


@dataclass
class ProcessRefinerResult:
    output_file_keys: list[str]
    metadata: RefinementMetadata


def process_refiner(input: ProcessRefinerInput) -> ProcessRefinerResult:
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
        ProcessedResult: the result of the refinement process
    """
    reportable_groups = discover_reportable_conditions(input.xml_files)
    logger.info(
        "Discovered reportable conditions from RR",
        reportable_group_payload=reportable_groups,
        operation="discovered_reportability",
    )

    # mutable state that is updated during the refinement process
    state = RefinementState()

    for jurisdiction_group in reportable_groups:
        process_jurisdiction(
            jurisdiction_group=jurisdiction_group,
            refiner_input=input,
            state=state,
        )

    write_unrefined_rrs(
        refiner_input=input,
        state=state,
    )

    log_refinement_summary(
        persistence_id=input.persistence_id,
        output_files=state.output_files,
        traces=state.traces,
    )

    return ProcessRefinerResult(
        output_file_keys=list(set(state.output_files)), metadata=state.metadata
    )


def process_jurisdiction(
    jurisdiction_group: JurisdictionReportableConditions,
    refiner_input: ProcessRefinerInput,
    state: RefinementState,
) -> None:
    """
    Process all reportable conditions for a single jurisdiction.
    """
    jurisdiction_code = jurisdiction_group.jurisdiction.upper()
    state.metadata.setdefault(jurisdiction_code, {})

    rsg_cg_payload = load_condition_mapping_for_jurisdiction(
        s3_client=refiner_input.s3_client,
        config_bucket=refiner_input.config_bucket_name,
        jurisdiction_code=jurisdiction_code,
    )

    if rsg_cg_payload is None:
        skip_all_conditions_for_missing_mapping(
            jurisdiction_code=jurisdiction_code,
            jurisdiction_group=jurisdiction_group,
            state=state,
        )
        return

    for reportable_condition in jurisdiction_group.conditions:
        process_condition(
            jurisdiction_code=jurisdiction_code,
            reportable_condition=reportable_condition,
            rsg_cg_payload=rsg_cg_payload,
            refiner_input=refiner_input,
            state=state,
        )


def load_condition_mapping_for_jurisdiction(
    s3_client,
    config_bucket: str,
    jurisdiction_code: str,
) -> ConditionMappingPayload | None:
    """
    Load the RSG -> CG mapping payload for a jurisdiction.
    """
    rsg_cg_mapping_file_key = get_rsg_cg_mapping_file_key(
        jurisdiction_id=jurisdiction_code
    )
    rsg_cg_mapping = read_rsg_cg_mapping_file(
        s3_client=s3_client,
        bucket=config_bucket,
        key=rsg_cg_mapping_file_key,
    )

    if not rsg_cg_mapping:
        logger.info(
            "Mapping file is empty or does not exist, skipping processing for jurisdiction.",
            key=rsg_cg_mapping_file_key,
            jurisdiction_code=jurisdiction_code,
            operation="skipped",
        )
        return None

    return ConditionMappingPayload.from_dict(rsg_cg_mapping)


def skip_all_conditions_for_missing_mapping(
    jurisdiction_code: str,
    jurisdiction_group: JurisdictionReportableConditions,
    state: RefinementState,
) -> None:
    """
    Mark every condition in a jurisdiction as skipped when the mapping file is missing.
    """
    for condition in jurisdiction_group.conditions:
        trace = RefinementTrace(
            jurisdiction_code=jurisdiction_code,
            rsg_code=condition.code,
            refinement_outcome="skipped",
            skip_reason="no_mapping_file",
        )
        state.traces.append(trace)
        state.non_active_reportable_conditions[jurisdiction_code].add(condition.code)
        state.metadata[jurisdiction_code][condition.code] = False


def process_condition(
    jurisdiction_code: str,
    reportable_condition: ReportableCondition,
    rsg_cg_payload: ConditionMappingPayload,
    refiner_input: ProcessRefinerInput,
    state: RefinementState,
) -> None:
    """
    Process a single reportable condition for a jurisdiction.
    """
    rsg_code = reportable_condition.code
    trace = RefinementTrace(
        jurisdiction_code=jurisdiction_code,
        rsg_code=rsg_code,
    )

    cg_metadata = rsg_cg_payload.mappings.get(rsg_code)

    if cg_metadata is None:
        logger.info(
            "RSG code isn't in the CG map, skipping.",
            rsg_code=rsg_code,
            rsg_cg_payload=rsg_cg_payload.to_dict(),
            jurisdiction_code=jurisdiction_code,
            operation="skipped",
        )
        mark_condition_skipped(
            trace=trace,
            jurisdiction_code=jurisdiction_code,
            condition_code=rsg_code,
            reason="rsg_not_in_mapping",
            state=state,
        )
        return

    trace.condition_grouper_name = cg_metadata.name

    processed_configuration = load_active_configuration(
        s3_client=refiner_input.s3_client,
        config_bucket=refiner_input.config_bucket_name,
        jurisdiction_code=jurisdiction_code,
        cg_metadata=cg_metadata,
        rsg_metadata=reportable_condition,
        trace=trace,
    )

    if processed_configuration is None:
        mark_condition_skipped(
            trace=trace,
            jurisdiction_code=jurisdiction_code,
            condition_code=rsg_code,
            reason="no_active_configuration",
            state=state,
        )
        return

    result = refine_for_condition(
        xml_files=refiner_input.xml_files,
        processed_configuration=processed_configuration,
        trace=trace,
    )

    state.traces.append(trace)

    write_refined_outputs(
        s3_client=refiner_input.s3_client,
        output_bucket_name=refiner_input.output_bucket_name,
        persistence_id=refiner_input.persistence_id,
        jurisdiction_code=jurisdiction_code,
        condition_grouper_name=cg_metadata.name,
        result=result,
        trace=trace,
        condition_code=rsg_code,
        state=state,
    )

    state.metadata[jurisdiction_code][rsg_code] = True


def mark_condition_skipped(
    trace: RefinementTrace,
    jurisdiction_code: str,
    condition_code: str,
    reason: str,
    state: RefinementState,
) -> None:
    """
    Centralize bookkeeping for skipped conditions.
    """
    trace.refinement_outcome = "skipped"
    trace.skip_reason = reason

    state.traces.append(trace)
    state.metadata[jurisdiction_code][condition_code] = False
    state.non_active_reportable_conditions[jurisdiction_code].add(condition_code)


def load_active_configuration(
    s3_client,
    config_bucket: str,
    jurisdiction_code: str,
    cg_metadata: ConditionMapValue,
    rsg_metadata: ReportableCondition,
    trace: RefinementTrace,
) -> ProcessedConfiguration | None:
    """
    Resolve and load the active processed configuration for a jurisdiction/condition.
    """
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
        logger.info(
            "No active configuration identified, skipping.",
            key=current_file_key,
            jurisdiction_code=jurisdiction_code,
            rsg_metadata=rsg_metadata,
            operation="skipped",
        )
        return None

    trace.configuration_version = config_version_to_use

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
        rsg_code=rsg_metadata.code,
        config_version=config_version_to_use,
        operation="activation_file_read",
    )

    return ProcessedConfiguration.from_dict(serialized_configuration)


def write_refined_outputs(
    s3_client,
    output_bucket_name: str,
    persistence_id: str,
    jurisdiction_code: str,
    condition_code: str,
    condition_grouper_name: str,
    result: RefinementResult,
    trace: RefinementTrace,
    state: RefinementState,
) -> None:
    """
    Write refined eICR and RR artifacts to S3.
    """
    output_key = (
        f"{REFINER_OUTPUT_PREFIX}"
        f"{persistence_id}/{jurisdiction_code}/{condition_grouper_name}"
    )

    eicr_output_key = f"{output_key}/refined_eICR.xml"
    s3_client.put_object(
        Bucket=output_bucket_name,
        Key=eicr_output_key,
        Body=result.refined_eicr.encode("utf-8"),
        ContentType="application/xml",
    )

    state.output_files.append(eicr_output_key)

    rr_output_key = f"{output_key}/refined_RR.xml"
    s3_client.put_object(
        Bucket=output_bucket_name,
        Key=rr_output_key,
        Body=result.refined_rr.encode("utf-8"),
        ContentType="application/xml",
    )

    state.output_files.append(rr_output_key)

    logger.info(
        "Condition refinement complete.",
        eicr_key=eicr_output_key,
        rr_key=rr_output_key,
        eicr_size_reduction_percentage=trace.eicr_size_reduction_percentage,
        jurisdiction_code=jurisdiction_code,
        condition_code=condition_code,
        operation="condition_refinement_complete",
    )


def write_unrefined_rrs(
    refiner_input: ProcessRefinerInput,
    state: RefinementState,
) -> None:
    """
    Write unrefined RR outputs for conditions that were skipped due to missing or
    inactive configuration.
    """
    for (
        jurisdiction_code,
        condition_codes,
    ) in state.non_active_reportable_conditions.items():
        unrefined_rr_content = refine_rr_for_unconfigured_conditions(
            xml_files=refiner_input.xml_files,
            condition_codes=condition_codes,
        )

        output_key = f"{REFINER_OUTPUT_PREFIX}{refiner_input.persistence_id}/{jurisdiction_code}/unrefined_rr"
        rr_output_key = f"{output_key}/refined_RR.xml"

        refiner_input.s3_client.put_object(
            Bucket=refiner_input.output_bucket_name,
            Key=rr_output_key,
            Body=unrefined_rr_content.encode("utf-8"),
            ContentType="application/xml",
        )
        state.output_files.append(rr_output_key)

        logger.info(
            "Created unrefined conditions RR",
            output_key=rr_output_key,
            jurisdiction_code=jurisdiction_code,
            condition_codes=list(condition_codes),
            operation="unrefined_conditions_rr_written",
        )


def log_refinement_summary(
    persistence_id: str,
    output_files: list[str],
    traces: list[RefinementTrace],
) -> None:
    """
    Log a final summary for the entire refinement run.
    """
    logger.info(
        "Refinement complete.",
        persistence_id=persistence_id,
        output_file_urls=output_files,
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
            for t in traces
        ],
        operation="refinement_complete",
    )


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
            result = process_refiner(
                xml_files,
                s3_client,
                s3_bucket_name,
                s3_config_bucket_name,
                persistence_id,
            )

            # Create RefinerComplete file
            complete_file: RefinerCompleteFile = {
                "RefinerMetadata": result.metadata,
                "RefinerSkip": False,
                "RefinerOutputFiles": result.output_file_keys,
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
                f"Successfully processed {len(result.output_file_keys)} refined outputs"
            )

        return {"statusCode": 200, "message": "Refiner processed successfully"}

    except Exception as e:
        logger.error(f"Error processing: {str(e)}", exception=e)
        raise

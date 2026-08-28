import json
from pathlib import Path

import psycopg
from config import TES_DATA_DIR, logger

from .models import (
    CODE_SYSTEM_DATA,
    DATETIME_VERSION_REGEX,
    SEMVER_VERSION_REGEX,
    SYSTEM_MAP,
    VERSION_REGEX,
    ConditionCodePayload,
    FhirCodeInfo,
    SystemSortedFhirInfo,
    VsCanonicalUrl,
    VsDict,
    VsVersion,
)
from .tes_parsing import get_tes_version


def get_db_connection(db_url: str, db_password: str) -> psycopg.Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.
    """

    try:
        return psycopg.connect(db_url, password=db_password)
    except psycopg.OperationalError as error:
        logger.error(f"❌ Database connection failed: {error}")
        raise


def categorize_codes_by_system(
    all_codes: set[FhirCodeInfo],
) -> ConditionCodePayload:
    """
    Categorizes a set of codes into a dictionary based on their system.
    """

    # the key is a "system_name", and the value is an empty list that will hold CodePayloads
    result: ConditionCodePayload = {
        system_name: [] for system_name in SYSTEM_MAP.values()
    }

    for info in all_codes:
        if system_key := SYSTEM_MAP.get(info.system_url):
            result[system_key].append(
                {
                    "code": info.code,
                    "display": info.display,
                }
            )

    return result


def categorize_codes_by_system_oid(
    all_codes: set[FhirCodeInfo],
) -> SystemSortedFhirInfo:
    """
    Categorizes a set of codes into a dictionary based on their system.
    """
    url_to_oid_map = {c["url"]: c["oid"] for c in CODE_SYSTEM_DATA.values()}
    # the key is a "system_name", and the value is an empty list that will hold CodePayloads
    result: SystemSortedFhirInfo = {
        system_oid: [] for system_oid in url_to_oid_map.values()
    }

    for info in all_codes:
        if cur_code_system_oid := url_to_oid_map.get(info.system_url):
            result[cur_code_system_oid].append(info)
    return result


def collect_files_to_parse(seed_all_tes_data: bool, versions_to_keep=2) -> list[Path]:
    """
    Function to collect the relevant files to seed, filtering out only the previous two TES releases to speed up local dev.
    """
    json_files = [f for f in TES_DATA_DIR.glob("*.json") if f.name != "manifest.json"]
    if seed_all_tes_data:
        return json_files

    # match on either TES semver version or the datetime string

    unique_versions_semver = {
        ver
        for f in json_files
        if (ver := get_tes_version(f.name, SEMVER_VERSION_REGEX))
    }
    unique_versions_datetime = {
        ver
        for f in json_files
        if (ver := get_tes_version(f.name, DATETIME_VERSION_REGEX))
    }
    top_versions = set(
        sorted(unique_versions_semver, reverse=True)[0:versions_to_keep]
    ) | set(sorted(unique_versions_datetime, reverse=True)[0:versions_to_keep])

    return [
        f for f in json_files if get_tes_version(f.name, VERSION_REGEX) in top_versions
    ]


def load_valuesets_from_all_files(
    seed_all_tes_data=False,
) -> dict[tuple[VsCanonicalUrl, VsVersion], VsDict]:
    """
    Loads all ValueSet resources from JSON files in the TES data directory.
    """

    vs_map: dict[tuple[str, str], dict] = {}
    json_files = collect_files_to_parse(seed_all_tes_data=seed_all_tes_data)

    for idx, file_path in enumerate(json_files, start=1):
        logger.info(f"📝 Loading TES file {idx} / {len(json_files)}: {file_path.name}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        for vs_dict in data.get("valuesets", []):
            url = vs_dict.get("url")
            version = vs_dict.get("version")
            if url and version:
                vs_map[(url, version)] = vs_dict
            else:
                logger.warning(f"Failed to parse ValueSet {url}|{version}")

    logger.info(f"📊 Loaded {len(vs_map)} unique ValueSets from all TES files.")
    return vs_map

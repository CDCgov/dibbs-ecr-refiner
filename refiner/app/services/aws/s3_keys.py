from app.services.conditions import extract_uuid_from_canonical_url

S3_CONFIGURATION_DIR_PREFIX = "configurations"


def get_jurisdiction_directory(jurisdiction_id: str) -> str:
    """
    Returns the jurisdiction's S3 directory path.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction

    Returns:
        str: Full S3 key to the jurisdiction directory.
    """
    return f"{S3_CONFIGURATION_DIR_PREFIX}/{jurisdiction_id}"


def get_parent_directory_key(jurisdiction_id: str, canonical_url: str) -> str:
    """
    Returns the "parent" directory where the activation files live.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        canonical_url (str): The condition canonical URL

    Returns:
        str: Full S3 key to the activation file parent directory
    """
    uuid = extract_uuid_from_canonical_url(url=canonical_url)
    return f"{get_jurisdiction_directory(jurisdiction_id=jurisdiction_id)}/{uuid}"


def get_rsg_cd_mapping_file_key(jurisdiction_id: str) -> str:
    """
    Constructs and returns the key to a jurisdiction's condition mapping file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction

    Returns:
        str: Full S3 key to a jurisdiction's rsg_cg_mapping.json file
    """
    return f"{get_jurisdiction_directory(jurisdiction_id=jurisdiction_id)}/rsg_cg_mapping.json"


def get_active_file_key(jurisdiction_id: str, canonical_url: str, version: int) -> str:
    """
    Constructs and returns the key to a configuration activation file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        canonical_url (str): The condition canonical URL
        version (int): The configuration version

    Returns:
        str: Full S3 key to an active.json configuration file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, canonical_url=canonical_url)}/{version}/active.json"


def get_metadata_file_key(
    jurisdiction_id: str, canonical_url: str, version: int
) -> str:
    """
    Constructs and returns the key to a configuration metadata file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        canonical_url (str): The condition canonical URL
        version (int): The configuration version

    Returns:
        str: Full S3 key to a metadata.json file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, canonical_url=canonical_url)}/{version}/metadata.json"


def get_current_file_key(jurisdiction_id: str, canonical_url: str) -> str:
    """
    Constructs and returns the key to a current version file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        canonical_url (str): The condition canonical URL
        version (int): The configuration version

    Returns:
        str: Full S3 key to a current.json file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, canonical_url=canonical_url)}/current.json"

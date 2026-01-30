S3_CONFIGURATION_DIR_PREFIX = "configurations"


def get_parent_directory_key(jurisdiction_id: str, rsg_code: str) -> str:
    """
    Returns the "parent" directory where the activation files live.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        rsg_code (str): The RSG code

    Returns:
        str: Full S3 key to the activation file parent directory
    """
    return f"{S3_CONFIGURATION_DIR_PREFIX}/{jurisdiction_id}/{rsg_code}"


def get_active_file_key(jurisdiction_id: str, rsg_code: str, version: int) -> str:
    """
    Constructs and returns the key to a configuration activation file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        rsg_code (str): The RSG code
        version (int): The configuration version

    Returns:
        str: Full S3 key to an active.json configuration file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, rsg_code=rsg_code)}/{version}/active.json"


def get_metadata_file_key(jurisdiction_id: str, rsg_code: str, version: int) -> str:
    """
    Constructs and returns the key to a configuration metadata file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        rsg_code (str): The RSG code
        version (int): The configuration version

    Returns:
        str: Full S3 key to a metadata.json file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, rsg_code=rsg_code)}/{version}/metadata.json"


def get_current_file_key(jurisdiction_id: str, rsg_code: str) -> str:
    """
    Constructs and returns the key to a current version file.

    Args:
        jurisdiction_id (str): The ID of the jurisdiction
        rsg_code (str): The RSG code
        version (int): The configuration version

    Returns:
        str: Full S3 key to a current.json file
    """
    return f"{get_parent_directory_key(jurisdiction_id=jurisdiction_id, rsg_code=rsg_code)}/current.json"

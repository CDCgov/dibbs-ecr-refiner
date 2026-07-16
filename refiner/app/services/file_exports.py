from datetime import UTC, datetime


def get_export_timestamp() -> str:
    """
    Calculates and returns a timestamp to use in file export names.

    Returns:
        str: The timestamp as a string
    """
    now = datetime.now(UTC)
    timestamp = now.strftime("%m%d%y_%H_%M_%S")
    return timestamp

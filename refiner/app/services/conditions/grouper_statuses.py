from typing import Literal

type CodeSetStatus = Literal["not expanded", "partially complete", "fully complete"]


def get_code_set_status(coverage_level: str | None) -> CodeSetStatus:
    """
    Given a string, attempts to return a code set status.

    Defaults to returning `not expanded`.

    Args:
        coverage_level (str | None): The coverage level text

    Returns:
        CodeSetStatus: The status string
    """
    if coverage_level == "complete":
        return "fully complete"

    if coverage_level == "partial":
        return "partially complete"

    return "not expanded"

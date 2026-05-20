import re
import unicodedata


def get_computed_condition_name(condition_name: str) -> str:
    """
    Given a condition name returns the computed name.

    For example:
    - `COVID-19` becomes `COVID19`
    - `Drowning and Submersion` becomes `DrowningandSubmersion`

    Args:
        condition_name (str): The name of the condition

    Returns:
        str: The computed condition name
    """
    # !!NOTE!!
    # TES versions 1-3 have the computed name `Tickborne_relapsing_feverTBRF` and
    # version 4 has the computed name `Tickborne_relapsing_fever_TBRF` which is probably a bug

    normalized = unicodedata.normalize("NFKD", condition_name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"\s+", "", normalized.strip())
    normalized = re.sub(r"[^A-Za-z0-9_]", "", normalized)
    return normalized

from urllib.parse import urlparse
from uuid import UUID

from app.db.configurations.model import NO_CONDITION_SENTINEL


def extract_uuid_from_canonical_url(canonical_url: str | None) -> str:
    """
    Given a `canonical_url`, extracts and returns the UUID at the end of it as a string.

    For example, given `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/c435a017-41e6-4030-b6d1-0bda2eb05b1f`
    the function returns `"c435a017-41e6-4030-b6d1-0bda2eb05b1f"`

    If `canonical_url` is `None`, `"N/A"`, or empty, returns `NO_CONDITION_SENTINEL`.
    If the UUID extraction fails, returns `NO_CONDITION_SENTINEL`.

    Args:
        canonical_url (str | None): The canonical URL

    Returns:
        str: The UUID at the end of the canonical URL, or `NO_CONDITION_SENTINEL` if not extractable
    """
    if not canonical_url or canonical_url == "N/A":
        return NO_CONDITION_SENTINEL

    try:
        parsed = urlparse(canonical_url)
        last_segment = parsed.path.rstrip("/").split("/")[-1]
        return str(UUID(last_segment))
    except ValueError:
        return NO_CONDITION_SENTINEL

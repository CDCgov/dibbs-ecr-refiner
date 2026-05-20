from urllib.parse import urlparse
from uuid import UUID


def extract_uuid_from_canonical_url(canonical_url: str) -> UUID:
    """
    Given a `canonical_url`, extracts and returns the UUID at the end of it.

    For example, given `https://tes.tools.aimsplatform.org/api/fhir/ValueSet/c435a017-41e6-4030-b6d1-0bda2eb05b1f`
    the function returns `c435a017-41e6-4030-b6d1-0bda2eb05b1f`

    Args:
        canonical_url (str): The canonical URL

    Returns:
        UUID: The UUID at the end of the canonical URL
    """
    parsed = urlparse(canonical_url)
    last_segment = parsed.path.rstrip("/").split("/")[-1]
    return UUID(last_segment)

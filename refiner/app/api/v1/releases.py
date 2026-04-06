import re
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, TypeAdapter

router = APIRouter(prefix="/releases")


@dataclass
class GithubReleaseResponse(BaseModel):
    """
    Type for release information coming from the GitHub API.
    """

    created_at: datetime
    name: str
    body: str
    prerelease: bool
    html_url: str
    # type out more properties as needed by the frontend


@dataclass
class ReleaseNotes:
    """
    Content of a release note from GitHub.
    """

    id: str
    content: str


@dataclass
class Release:
    """
    Type for release information sent to the frontend.
    """

    id: str
    created_at: datetime
    name: str
    # ReleaseNotes are indexed by the most adjacent <h[1-6]> # from GitHub
    release_notes: dict[str, ReleaseNotes]
    prerelease: bool
    url: str


@dataclass
class ReleasesResponse:
    """
    Response for releases as returned through the GitHub API.
    """

    releases: list[Release]


@router.get(
    "/",
    tags=["releases"],
    response_model=ReleasesResponse,
    operation_id="getReleases",
)
async def get_releases_data() -> ReleasesResponse:
    """
    Hook to get release data from GitHub and serve it to the frontend.

    Returns:
        ReleasesResponse: Reponse of release information in a list of ReleaseMetadata
    """
    try:
        github_releases_data = _get_releases_data_from_github(ttl_hash=_get_ttl_hash())
    except ValueError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)

    return ReleasesResponse(releases=github_releases_data)


def _get_ttl_hash(period_to_invalidate_in_seconds: int = 300) -> int:
    """Utility function that returns the same value every period to help with cache invalidation.

    Args:
       period_to_invalidate_in_seconds: period to invalidate the cache in seconds.
       Defaults to 300 seconds or five minutes

    Returns:
        An int value that is consistent within a period of time. When consumed by
        an lru_cache decorated function as a parameter, will flush the cache
    """
    return int(time.time() // period_to_invalidate_in_seconds)


@lru_cache(maxsize=1)
def _get_releases_data_from_github(
    ttl_hash: int | None = None,
) -> list[Release]:
    """
    Function to fetch releases data from GitHub.

    Results are cached every hour to prevent rate limitting from the GitHub API

    Args:
        ttl_hash: Dummy parameter to force the lru_cache, which stores results based on parameters,
        to refresh if provided

    Returns:
        list[GithubReleaseObject]: A list of all releases as returned by a call to the GitHub API
    """
    # throw away param to make mypy happy
    del ttl_hash
    releases_endpoint = "https://api.github.com/repos/cdcgov/dibbs-ecr-refiner/releases"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    try:
        r = httpx.get(
            releases_endpoint,
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub returned error {exc.response.status_code}",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error connecting to GitHub",
        )

    release_json = r.json()
    if not isinstance(release_json, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Expected a list of releases from GitHub",
        )

    releases = TypeAdapter(list[GithubReleaseResponse]).validate_python(release_json)
    application_release_data: list[Release] = []

    for release in releases:
        if release.prerelease:
            continue

        release_content = release.body

        if not release_content:
            continue

        release_notes = _format_api_body_to_dict(release_content)
        release_object = Release(
            id=str(uuid4()),
            created_at=release.created_at,
            name=release.name,
            release_notes=release_notes,
            prerelease=release.prerelease,
            url=release.html_url,
        )
        application_release_data.append(release_object)

    return application_release_data


def _format_api_body_to_dict(content: str) -> dict[str, ReleaseNotes]:
    """
    Utility function to parse out string of markdown content in GitHub into key-value dict.

    String is split based on the # values in markdown denoting headers

    Args:
        content: str - string from GitHub releases API that has release content

    Returns:
        dict[str, str]: A { header:content} dict based on the # values from GitHub
    """
    # split out pieces of the release notes based on ## headers
    parts = re.split(r"(?m)^(#+ .*)$", content)
    parts = [p.strip() for p in parts if p.strip()]

    result: dict[str, ReleaseNotes] = {}

    for i in range(0, len(parts), 2):
        header = parts[i]
        section_content = parts[i + 1] if i + 1 < len(parts) else ""
        notes_content = ReleaseNotes(id=str(uuid4()), content=section_content.strip())
        result[header] = notes_content

    return result

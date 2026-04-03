import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import TypedDict

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from packaging.version import parse

from app.api.auth.middleware import get_logged_in_user
from app.core.config import ENVIRONMENT
from app.db.conditions.db import get_loaded_tes_versions_db
from app.db.configurations.db import get_configurations_db
from app.db.pool import AsyncDatabaseConnection, get_db
from app.db.schema_migrations.db import get_latest_migration_db
from app.db.users.model import DbUser

router = APIRouter(prefix="/info")


@dataclass
class GithubReleaseObject(TypedDict):
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
class ReleasesResponse:
    """
    Response for releases as returned through the GitHub API.
    """

    releases: list[GithubReleaseObject]


@router.get("", tags=["info", "internal"], include_in_schema=False)
async def get_info(
    user: DbUser = Depends(get_logged_in_user),
    db: AsyncDatabaseConnection = Depends(get_db),
) -> JSONResponse:
    """
    Fetch application state information for debugging purposes.

    Args:
        user (DbUser, optional): The logged-in user.
        db (AsyncDatabaseConnection, optional): The database connection.
        logger (Logger, optional): The app logger.

    Returns:
        JSONResponse: Application state information.
    """

    configs = await get_configurations_db(jurisdiction_id=user.jurisdiction_id, db=db)
    total_config_count = len(configs)
    total_active_config_count = len([c for c in configs if c.status == "active"])

    # minimal response to send to the client
    config_details = [
        {"name": config.name, "status": config.status, "version": config.version}
        for config in configs
    ]

    tes_versions = await get_loaded_tes_versions_db(db=db)
    latest_tes_version = max(tes_versions, key=lambda v: parse(v))

    return JSONResponse(
        content={
            "app": {
                "environment": ENVIRONMENT["ENV"],
                "version": ENVIRONMENT["VERSION"],
            },
            "data": {
                "revision": await get_latest_migration_db(db=db),
                "tes_versions": tes_versions,
                "latest_tes_version": latest_tes_version,
            },
            "session": {
                "username": user.username,
                "jurisdiction_id": user.jurisdiction_id,
                "configurations": {
                    "total_count": total_config_count,
                    "active_count": total_active_config_count,
                    "detail": config_details,
                },
            },
        }
    )


@router.get(
    "/releases",
    tags=["info"],
    response_model=ReleasesResponse,
    operation_id="getReleasesData",
)
async def get_releases_data() -> ReleasesResponse:
    """
    Hook to get release data from GitHub and serve it to the frontend.

    Returns:
        ReleasesResponse: Reponse of release information in a list of GithubReleaseObject
    """
    github_releases_data = get_releases_data_from_github(ttl_hash=get_ttl_hash())
    data: ReleasesResponse = ReleasesResponse(releases=github_releases_data)
    return data


def get_ttl_hash(period_to_invalidate_in_seconds: int = 300) -> float:
    """Utility function that returns the same value every period to help with cache invalidation.

    Args:
       period_to_invalidate_in_seconds: period to invalidate the cache in seconds.
       Defaults to 300 seconds or five minutes

    Returns:
        A float value that is consistent within a period of time. When consumed by
        an lru_cache decorated function as a parameter, will flush the cache
    """
    return time.time() // period_to_invalidate_in_seconds


@lru_cache
def get_releases_data_from_github(
    ttl_hash: int | None = None,
) -> list[GithubReleaseObject]:
    """
    Function to fetch releases data from GitHub.

    Results are cached every hour to prevent rate limitting from the GitHub API

    Args:
        ttl_hash: Dummy parameter to force the lru_cache, which stores results based on parameters,
        to refresh if provided

    Returns:
        list[GithubReleaseObject]: A list of all releases as returned by a call to the GitHub API
    """
    del ttl_hash
    releases_endpoint = "https://api.github.com/repos/cdcgov/dibbs-ecr-refiner/releases"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    r = requests.get(releases_endpoint, headers=headers)

    if r.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting information from GitHub",
        )

    github_releases_data: list[GithubReleaseObject] = r.json()

    for release_data in github_releases_data:
        release_content = release_data.get("body")
        if not release_content:
            continue

        formatted_body = format_notes_to_header_content_dict(release_content)
        if formatted_body:
            release_data["body"] = json.dumps(formatted_body)

    return github_releases_data


def format_notes_to_header_content_dict(content: str) -> dict[str, str]:
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

    result = {}

    for i in range(0, len(parts), 2):
        header = parts[i]
        section_content = parts[i + 1] if i + 1 < len(parts) else ""
        result[header] = section_content.strip()

    return result

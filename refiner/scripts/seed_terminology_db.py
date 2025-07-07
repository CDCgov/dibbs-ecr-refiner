import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
import requests
from dotenv import load_dotenv


@dataclass
class CodeableConcept:
    """
    Type for a code entry in the terminology system.
    """

    code: str
    display: str


@dataclass
class ValueSetCompose:
    """
    Type for FHIR ValueSet compose section.
    """

    include: list[dict[str, Any]]


@dataclass
class ValueSetResource:
    """
    Type for a FHIR ValueSet resource.
    """

    id: str
    title: str | None
    name: str | None
    compose: ValueSetCompose

    def get(self, key: str, default: Any = None) -> Any:
        """
        Mimic dict.get() for compatibility.
        """

        return getattr(self, key, default)


@dataclass
class TESResponse:
    """
    Type for TES API response.
    """

    entry: list[dict[str, ValueSetResource]]
    link: list[dict[str, str]]


class TESDataLoader:
    """
    TES Data Loader for populating groupers and filters tables with RS-groupers.
    """

    def __init__(self, db_url) -> None:
        """
        Initialize the TES Data Loader with database connection and API configuration.

        This constructor:
        1. Loads environment variables for API configuration
        2. Sets up API connection headers
        3. Initializes database connection
        4. Configures logging
        5. Creates required database tables

        Args:
            db_url: PostgreSQL database URL

        Environment Variables Used:
            TES_API_URL: Base URL for the TES API
            TES_API_KEY: Authentication key for the TES API
            API_SLEEP_INTERVAL: Time to wait between API calls (default: 1.0)

        Note:
            Ensure .env file contains required API credentials before initialization.
        """

        self.api_url: str = os.getenv("TES_API_URL", "")
        self.api_key: str = os.getenv("TES_API_KEY", "")
        self.sleep_interval: float = float(os.getenv("API_SLEEP_INTERVAL", "1.0"))
        self.headers: dict[str, str] = {
            "X-API-KEY": self.api_key,
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        self.db_url = db_url
        self.connection = psycopg.connect(self.db_url, autocommit=True)
        self.setup_logging()
        self.create_tables()

    def setup_logging(self) -> None:
        """
        Set up logging configuration.
        """

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger: logging.Logger = logging.getLogger(__name__)

    def create_tables(self) -> None:
        """
        Create the groupers and filters tables.
        """

        self.logger.info("Creating database tables if they don't exist")

        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        schema_path = project_root / "app" / "db" / "schema.sql"

        with schema_path.open() as f:
            with self.connection.cursor() as cursor:
                cursor.execute(f.read())

    def store_grouper(
        self,
        condition: str,
        display_name: str,
        loinc_codes: list[CodeableConcept],
        snomed_codes: list[CodeableConcept],
        icd10_codes: list[CodeableConcept],
        rxnorm_codes: list[CodeableConcept],
    ) -> None:
        """Store a grouper in the database."""
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO groupers (
                    condition, display_name, loinc_codes,
                    snomed_codes, icd10_codes, rxnorm_codes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (condition) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    loinc_codes = EXCLUDED.loinc_codes,
                    snomed_codes = EXCLUDED.snomed_codes,
                    icd10_codes = EXCLUDED.icd10_codes,
                    rxnorm_codes = EXCLUDED.rxnorm_codes
                """,
                (
                    condition,
                    display_name,
                    json.dumps([c.__dict__ for c in loinc_codes]),
                    json.dumps([c.__dict__ for c in snomed_codes]),
                    json.dumps([c.__dict__ for c in icd10_codes]),
                    json.dumps([c.__dict__ for c in rxnorm_codes]),
                ),
            )

    def store_filter(self, condition: str, display_name: str) -> None:
        """
        Store a default filter in the filters table.
        """

        default_included_groupers = [{"condition": condition, "display": display_name}]
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO filters (
                    condition, display_name, ud_loinc_codes,
                    ud_snomed_codes, ud_icd10_codes,
                    ud_rxnorm_codes, included_groupers
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (condition) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    included_groupers = EXCLUDED.included_groupers
                """,
                (
                    condition,
                    display_name,
                    "[]",
                    "[]",
                    "[]",
                    "[]",
                    json.dumps(default_included_groupers),
                ),
            )

    def make_tes_request(
        self, endpoint: str, params: dict[str, str | int] | None = None
    ) -> dict[str, Any]:
        """
        Make rate-limited request to TES API.
        """

        time.sleep(self.sleep_interval)
        response = requests.get(
            f"{self.api_url}/{endpoint}",
            headers=self.headers,
            params=params or {},
        )
        response.raise_for_status()
        return response.json()

    def make_tes_request_from_url(self, url: str) -> dict[str, Any]:
        """
        Make a request to a full URL (e.g., for pagination).
        """

        time.sleep(self.sleep_interval)
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_next_url(self, response: dict[str, Any]) -> str | None:
        """
        Extract the next URL for pagination.
        """

        if "link" in response:
            for link in response["link"]:
                if link.get("relation") == "next":
                    return link.get("url")
        return None

    def extract_codes(
        self, resource: dict[str, Any]
    ) -> dict[str, list[CodeableConcept]]:
        """
        Extract codes from a ValueSet resource.

        Args:
            resource: FHIR ValueSet resource dictionary

        Returns:
            Dictionary mapping code types to lists of codes
        """

        codes: dict[str, list[CodeableConcept]] = {
            "loinc": [],
            "snomed": [],
            "icd10": [],
            "rxnorm": [],
        }

        compose = resource.get("compose", {})
        for include in compose.get("include", []):
            system_url: str = include.get("system", "")
            concepts: list[dict[str, str]] = include.get("concept", [])

            # initialize code_type to None
            code_type: str | None = None

            match system_url:
                case system_url if "loinc.org" in system_url:
                    code_type = "loinc"
                case system_url if "snomed.info" in system_url:
                    code_type = "snomed"
                case system_url if "icd-10-cm" in system_url:
                    code_type = "icd10"
                case system_url if "rxnorm" in system_url.lower():
                    code_type = "rxnorm"
                case _:
                    # there are many code systems we don't need that we'll simply pass on
                    # we just want the condition groupers
                    continue

            if not concepts:
                self.logger.error(
                    msg=f"No concepts found for system {system_url}",
                    extra={"code_type": code_type},
                )
                continue

            for concept in concepts:
                codeable = CodeableConcept(
                    code=concept["code"], display=concept.get("display", "")
                )
                codes[code_type].append(codeable)

        return codes

    def populate_groupers_and_filters(self) -> None:
        """
        Populate the groupers and filters tables with RS-groupers data from TES API.
        """

        self.logger.info("Populating groupers and filters tables")
        response = self.make_tes_request(
            "ValueSet", {"status": "active", "_count": 1000}
        )

        while response and "entry" in response:
            entries = response.get("entry", [])
            if not entries:
                break

            for entry in entries:
                resource = entry.get("resource", {})

                # ignore non-RS-groupers
                if not resource.get("compose") or not resource.get("id", "").startswith(
                    "rs-grouper"
                ):
                    continue

                # extract SNOMED code
                condition = resource.get("id", "").replace("rs-grouper-", "")

                # use `title`; `name` is rs-grouper+SNOMED
                display_name = resource.get("title") or resource.get("name", "")
                codes = self.extract_codes(resource)

                if condition and display_name:
                    self.store_grouper(
                        condition=condition,
                        display_name=display_name,
                        loinc_codes=codes["loinc"],
                        snomed_codes=codes["snomed"],
                        icd10_codes=codes["icd10"],
                        rxnorm_codes=codes["rxnorm"],
                    )

                    self.store_filter(condition=condition, display_name=display_name)

            # handle pagination
            next_url = self.get_next_url(response)
            if not next_url:
                break
            response = self.make_tes_request_from_url(next_url)

        self.logger.info("Finished populating groupers and filters tables")


def dump_postgres_db_from_url(conn_str: str, output_file: str):
    """
    Dumps a PostgreSQL database using docker-compose and pg_dump.

    Args:
        conn_str: PostgreSQL connection string (e.g. postgresql://user:pass@host:port/dbname).
        output_file: Path to save the dump file on the host.
    """
    # Grab user and database from connection string
    match = re.match(r"postgresql://([^:]+):[^@]+@[^/]+/([^?]+)", conn_str)
    if not match:
        raise ValueError("Invalid connection string format.", conn_str)

    user, dbname = match.groups()

    # Compose the command
    dump_cmd = f"docker-compose exec db pg_dump -U {user} {dbname} > {output_file}"

    try:
        print(f"Dumping database to: {output_file}")
        subprocess.run(dump_cmd, shell=True, check=True, executable="/bin/bash")
        print("Database dump completed")
    except subprocess.CalledProcessError as e:
        print(f"Error during pg_dump: {e}")
        raise


if __name__ == "__main__":
    load_dotenv()
    db_url = os.getenv("DB_URL")

    loader = TESDataLoader(db_url)
    loader.populate_groupers_and_filters()

    # DB dump is used to seed the database for integration tests
    dump_path = Path(__file__).parent / "seed-data.sql"
    dump_postgres_db_from_url(db_url, str(dump_path))

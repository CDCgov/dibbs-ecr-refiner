import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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

    def __init__(self, db_path: str, api_version: str = "1.0.0") -> None:
        """
        Initialize the TES Data Loader with database connection and API configuration.

        This constructor:
        1. Loads environment variables for API configuration
        2. Sets up API connection headers
        3. Initializes database connection
        4. Configures logging
        5. Creates required database tables

        Args:
            db_path: Path to the SQLite database file
            api_version: TES API version to use (default: "1.0.0")

        Environment Variables Used:
            TES_API_URL: Base URL for the TES API
            TES_API_KEY: Authentication key for the TES API
            API_SLEEP_INTERVAL: Time to wait between API calls (default: 1.0)

        Note:
            Ensure .env file contains required API credentials before initialization.
        """

        load_dotenv()
        self.api_url: str = os.getenv("TES_API_URL", "")
        self.api_key: str = os.getenv("TES_API_KEY", "")
        self.api_version: str = api_version
        self.sleep_interval: float = float(os.getenv("API_SLEEP_INTERVAL", "1.0"))
        self.headers: dict[str, str] = {
            "X-API-KEY": self.api_key,
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        self.db_path: str = db_path
        self.connection: sqlite3.Connection = sqlite3.connect(db_path)
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
            cursor = self.connection.cursor()
            # assign to _ to handle unused result
            _ = cursor.executescript(f.read())
            self.connection.commit()

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
        cursor = self.connection.cursor()
        # assign to _ to handle unused result
        _ = cursor.execute(
            """
            INSERT OR REPLACE INTO groupers (
                condition, display_name, loinc_codes,
                snomed_codes, icd10_codes, rxnorm_codes
            ) VALUES (?, ?, ?, ?, ?, ?)
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
        self.connection.commit()

    def store_filter(self, condition: str, display_name: str) -> None:
        """
        Store a default filter in the filters table.
        """

        cursor = self.connection.cursor()
        default_included_groupers = [{"condition": condition, "display": display_name}]
        # assign to _ to handle unused result
        _ = cursor.execute(
            """
            INSERT OR REPLACE INTO filters (
                condition, display_name, ud_loinc_codes,
                ud_snomed_codes, ud_icd10_codes,
                ud_rxnorm_codes, included_groupers
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
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
        self.connection.commit()

    def make_tes_request(
        self, endpoint: str, params: dict[str, str | int] | None = None
    ) -> dict[str, Any]:
        """
        Make rate-limited request to TES API.
        """

        time.sleep(self.sleep_interval)
        request_params = params or {}
        
        # Add version parameter for API v2.0.0+
        if self.api_version != "1.0.0":
            request_params["version"] = self.api_version
            
        response = requests.get(
            f"{self.api_url}/{endpoint}",
            headers=self.headers,
            params=request_params,
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

    def is_relevant_grouper(self, resource: dict[str, Any]) -> bool:
        """
        Check if a ValueSet resource is a relevant grouper based on API version.
        
        For v1.0.0: Check if ID starts with 'rs-grouper'
        For v2.0.0+: Check useContext for condition-grouper or additional-context-grouper
        """
        
        if self.api_version == "1.0.0":
            # Original v1.0.0 logic
            return (
                resource.get("compose") 
                and resource.get("id", "").startswith("rs-grouper")
            )
        else:
            # v2.0.0+ logic: check useContext
            use_context = resource.get("useContext", [])
            
            for context in use_context:
                if context.get("code", {}).get("code") == "task":
                    value_concept = context.get("valueCodeableConcept", {})
                    codings = value_concept.get("coding", [])
                    
                    for coding in codings:
                        if coding.get("code") in ["condition-grouper", "additional-context-grouper"]:
                            return True
            return False

    def extract_condition_from_resource(self, resource: dict[str, Any]) -> str | None:
        """
        Extract condition SNOMED code from resource based on API version.
        
        For v1.0.0: Extract from ID by removing 'rs-grouper-' prefix
        For v2.0.0+: Extract from useContext focus
        """
        
        if self.api_version == "1.0.0":
            # Original v1.0.0 logic
            resource_id = resource.get("id", "")
            if resource_id.startswith("rs-grouper-"):
                return resource_id.replace("rs-grouper-", "")
            return None
        else:
            # v2.0.0+ logic: extract from useContext
            use_context = resource.get("useContext", [])
            
            for context in use_context:
                if context.get("code", {}).get("code") == "focus":
                    value_concept = context.get("valueCodeableConcept", {})
                    codings = value_concept.get("coding", [])
                    
                    for coding in codings:
                        if "snomed.info/sct" in coding.get("system", ""):
                            return coding.get("code")
            return None

    def extract_codes(
        self, resource: dict[str, Any]
    ) -> dict[str, list[CodeableConcept]]:
        """
        Extract codes from a ValueSet resource.
        
        Handles both v1.0.0 structure (direct concepts) and v2.0.0 structure 
        (ValueSet references for main groupers, direct concepts for additional context).

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
            # Handle ValueSet references (v2.0.0 main groupers)
            if "valueSet" in include:
                # For now, we'll log ValueSet references but skip processing them
                # as they would require additional API calls to resolve
                self.logger.info(f"Found ValueSet references: {include['valueSet']}")
                continue
            
            # Handle direct concepts (v1.0.0 and v2.0.0 additional context groupers)
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
        
        For v2.0.0+: Groups multiple ValueSets per condition and combines their codes.
        """

        self.logger.info(f"Populating groupers and filters tables (API version: {self.api_version})")
        response = self.make_tes_request(
            "ValueSet", {"status": "active", "_count": 1000}
        )

        # For v2.0.0+, group resources by condition before processing
        condition_resources: dict[str, list[dict[str, Any]]] = {}

        while response and "entry" in response:
            entries = response.get("entry", [])
            if not entries:
                break

            for entry in entries:
                resource = entry.get("resource", {})

                # Apply version-appropriate filtering
                if not resource.get("compose") or not self.is_relevant_grouper(resource):
                    continue

                # Extract condition code
                condition = self.extract_condition_from_resource(resource)
                if not condition:
                    self.logger.warning(f"Could not extract condition from resource {resource.get('id', 'unknown')}")
                    continue

                # Group resources by condition (for v2.0.0+ handling multiple ValueSets per condition)
                if condition not in condition_resources:
                    condition_resources[condition] = []
                condition_resources[condition].append(resource)

            # handle pagination
            next_url = self.get_next_url(response)
            if not next_url:
                break
            response = self.make_tes_request_from_url(next_url)

        # Process grouped resources
        for condition, resources in condition_resources.items():
            self.logger.info(f"Processing condition {condition} with {len(resources)} ValueSet(s)")
            
            # Combine codes from all ValueSets for this condition
            combined_codes: dict[str, list[CodeableConcept]] = {
                "loinc": [],
                "snomed": [],
                "icd10": [],
                "rxnorm": [],
            }
            
            # Use the title from the first resource or fall back to name
            display_name = ""
            
            for resource in resources:
                resource_codes = self.extract_codes(resource)
                
                # Combine codes from all systems
                for system in combined_codes:
                    combined_codes[system].extend(resource_codes[system])
                
                # Use title from the first resource, prefer main grouper over additional context
                if not display_name or "Additional_Context" not in resource.get("title", ""):
                    display_name = resource.get("title") or resource.get("name", "")

            if condition and display_name:
                self.store_grouper(
                    condition=condition,
                    display_name=display_name,
                    loinc_codes=combined_codes["loinc"],
                    snomed_codes=combined_codes["snomed"],
                    icd10_codes=combined_codes["icd10"],
                    rxnorm_codes=combined_codes["rxnorm"],
                )

                self.store_filter(condition=condition, display_name=display_name)

        self.logger.info("Finished populating groupers and filters tables")


if __name__ == "__main__":
    import sys
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "app" / "terminology.db"

    # Allow version to be specified as command line argument
    api_version = "1.0.0"  # Default to v1.0.0 for backward compatibility
    if len(sys.argv) > 1:
        api_version = sys.argv[1]
    
    # Allow version to be specified via environment variable
    api_version = os.getenv("TES_API_VERSION", api_version)

    print(f"Using TES API version: {api_version}")
    loader = TESDataLoader(str(db_path), api_version=api_version)
    loader.populate_groupers_and_filters()

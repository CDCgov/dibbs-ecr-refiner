import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from fhir.resources.valueset import ValueSet
from psycopg import Connection, sql

# configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TES_DATA_DIR = DATA_DIR / "source-tes-groupers"
ENV_PATH = BASE_DIR / ".env"

# type aliases
# a tuple representing a single, raw code: (system, code, display) pulled straight from the fhir ValueSet
# * display **could** be empty
type FhirCodeTuple = tuple[str, str, str | None]

# a dictionary representing a single code prepared for categorization by a code system
# * display **could** be empty
type CodePayload = dict[str, str | None]

# a list of processed codes for a specific system
type SystemCodeList = list[CodePayload]

# the map of all unique codes for a condition + version
type ConditionCodePayload = dict[str, SystemCodeList]

SYSTEM_MAP = {
    "http://loinc.org": "loinc_codes",
    "http://snomed.info/sct": "snomed_codes",
    "http://hl7.org/fhir/sid/icd-10-cm": "icd10_codes",
    "http://www.nlm.nih.gov/research/umls/rxnorm": "rxnorm_codes",
}


@dataclass
class ConditionData:
    """
    Represents a single, processed condition grouper ready for database insertion.
    """

    parent_vs: ValueSet
    all_vs_map: dict[tuple[str, str], ValueSet]

    child_codes: set[FhirCodeTuple] = field(init=False, default_factory=set)
    """
    Codes from all child 'Reporting Specification Grouper' (RSG) ValueSets.
    """

    sibling_codes: set[FhirCodeTuple] = field(init=False, default_factory=set)
    """
    Codes from all sibling 'Additional Context Grouper' ValueSets.
    """

    child_rsg_snomed_codes: set[str] = field(init=False, default_factory=set)
    """
    SNOMED codes extracted directly from the URLs of child RSG ValueSets.
    """

    def __post_init__(self):
        """
        Populates the code sets after the instance is initialized.
        """

        self._aggregate_child_codes()
        self._aggregate_sibling_codes()

    def _aggregate_child_codes(self):
        """
        Extracts codes and SNOMED IDs from all child RSG ValueSets.
        """

        for child_vs in get_child_rsg_valuesets(self.parent_vs, self.all_vs_map):
            if snomed_code := parse_snomed_from_url(child_vs.url or ""):
                self.child_rsg_snomed_codes.add(snomed_code)
            self.child_codes.update(extract_codes_from_compose(child_vs))

    def _aggregate_sibling_codes(self):
        """
        Extracts codes from all sibling 'additional context' ValueSets.
        """

        for sib_vs in get_sibling_context_valuesets(self.parent_vs, self.all_vs_map):
            self.sibling_codes.update(extract_codes_from_compose(sib_vs))

    @property
    def payload(self) -> dict[str, Any]:
        """
        Generates the dictionary payload for database insertion.
        """

        # combine all codes; the union operator `|` correctly merges the sets
        all_codes = self.child_codes | self.sibling_codes
        categorized = categorize_codes_by_system(all_codes)
        return {
            "canonical_url": self.parent_vs.url,
            "version": self.parent_vs.version,
            "display_name": (self.parent_vs.title or self.parent_vs.name or "").replace(
                "_", " "
            ),
            "child_rsg_snomed_codes": list(self.child_rsg_snomed_codes),
            "loinc_codes": json.dumps(categorized["loinc_codes"]),
            "snomed_codes": json.dumps(categorized["snomed_codes"]),
            "icd10_codes": json.dumps(categorized["icd10_codes"]),
            "rxnorm_codes": json.dumps(categorized["rxnorm_codes"]),
        }


def get_db_connection(db_url: str, db_password: str) -> Connection:
    """
    Establishes and returns a connection to the PostgreSQL database.
    """

    try:
        return psycopg.connect(db_url, password=db_password)
    except psycopg.OperationalError as error:
        logger.error(f"❌ Database connection failed: {error}")
        raise


def load_valuesets_from_all_files() -> dict[tuple[str, str], ValueSet]:
    """
    Loads all ValueSet resources from JSON files in the TES data directory.
    """

    vs_map: dict[tuple[str, str], ValueSet] = {}
    json_files = [f for f in TES_DATA_DIR.glob("*.json") if f.name != "manifest.json"]
    for file_path in json_files:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        for vs_dict in data.get("valuesets", []):
            if (url := vs_dict.get("url")) and (version := vs_dict.get("version")):
                try:
                    vs_map[(url, version)] = ValueSet.model_validate(vs_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse ValueSet {url}|{version}: {e}")
    logger.info(f"Loaded {len(vs_map)} unique ValueSets from all TES files.")
    return vs_map


def is_condition_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is a 'ConditionGrouper' via its metadata profile.
    """

    profiles = getattr(getattr(vs, "meta", None), "profile", []) or []
    # we have to cast the return to make mypy happy
    return bool(any("conditiongroupervalueset" in str(prof) for prof in profiles))


def is_reporting_spec_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is a 'ReportingSpecGrouper' by its URL.
    """

    # we have to cast the return to make mypy happy
    return bool(vs.url and "rs-grouper" in vs.url.lower())


def is_additional_context_grouper(vs: ValueSet) -> bool:
    """
    Checks if a ValueSet is for 'Additional Context' by its name or title.
    """

    name = (vs.name or "").lower()
    title = (vs.title or "").lower()
    return "additional" in name or "additional" in title


def extract_codes_from_compose(vs: ValueSet) -> set[FhirCodeTuple]:
    """
    Extracts all (system, code, display) tuples from a ValueSet's compose section.
    """

    codes: set[FhirCodeTuple] = set()
    if vs.compose:
        for inc in vs.compose.include or []:
            if inc.system and inc.concept:
                for concept in inc.concept:
                    if concept.code:
                        codes.add((inc.system, concept.code, concept.display))
    return codes


def get_child_rsg_valuesets(
    parent: ValueSet, all_vs_map: dict[tuple[str, str], ValueSet]
) -> list[ValueSet]:
    """
    Finds all 'ReportingSpecGrouper' children of a parent ValueSet.
    """

    children: list[ValueSet] = []
    if parent.compose:
        for inc in parent.compose.include or []:
            for ref in inc.valueSet or []:
                url, sep, version = str(ref).partition("|")
                if sep and (child_vs := all_vs_map.get((url, version))):
                    if is_reporting_spec_grouper(child_vs):
                        children.append(child_vs)
    return children


def get_sibling_context_valuesets(
    parent: ValueSet, all_vs_map: dict[tuple[str, str], ValueSet]
) -> list[ValueSet]:
    """
    Finds sibling 'Additional Context' ValueSets by matching name and version.
    """

    siblings: list[ValueSet] = []
    parent_name = (parent.name or "").lower().replace("_", "")
    for vs in all_vs_map.values():
        if (
            is_additional_context_grouper(vs)
            and vs.version == parent.version
            and vs.url != parent.url
            and parent_name in (vs.name or "").lower().replace("_", "")
        ):
            siblings.append(vs)
    return siblings


def categorize_codes_by_system(all_codes: set[FhirCodeTuple]) -> ConditionCodePayload:
    """
    Categorizes a set of codes into a dictionary based on their system.
    """

    # the key is a "system_name", and the value is an empty list that will hold CodePayloads
    result: ConditionCodePayload = {
        system_name: [] for system_name in SYSTEM_MAP.values()
    }
    for system, code, display in all_codes:
        if system_key := SYSTEM_MAP.get(system):
            result[system_key].append({"code": code, "display": display})
    return result


def parse_snomed_from_url(url: str) -> str | None:
    """
    Extracts a SNOMED code from a 'rs-grouper' URL.
    """

    return url.split("rs-grouper-")[-1] if "rs-grouper-" in url else None


def seed_database(db_url: str, db_password: str) -> None:
    """
    Orchestrates the entire database seeding process.
    """

    logger.info("🚀 Starting database seeding...")
    all_vs_map = load_valuesets_from_all_files()

    condition_groupers = [vs for vs in all_vs_map.values() if is_condition_grouper(vs)]
    logger.info(f"Identified {len(condition_groupers)} condition groupers to process.")

    processed_conditions = [
        ConditionData(parent, all_vs_map) for parent in condition_groupers
    ]
    conditions_to_insert = [cond.payload for cond in processed_conditions]

    if not conditions_to_insert:
        logger.warning("⚠️ No conditions were processed. Aborting database write.")
        return

    logger.info(f"✅ Prepared {len(conditions_to_insert)} records for insertion.")
    try:
        with get_db_connection(db_url, db_password) as conn, conn.cursor() as cursor:
            logger.info("🧹 Clearing specified data tables...")
            tables_to_truncate = [
                "conditions",
                "jurisdictions",
                "configurations",
                "sessions",
                "users",
            ]
            for table in tables_to_truncate:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                except psycopg.errors.UndefinedTable:
                    logger.warning(f"Table '{table}' not found, skipping truncation.")

            logger.info("⏳ Inserting condition records...")
            insert_query = sql.SQL(
                """
                INSERT INTO public.conditions (canonical_url, version, display_name, child_rsg_snomed_codes, loinc_codes, snomed_codes, icd10_codes, rxnorm_codes)
                VALUES (%(canonical_url)s, %(version)s, %(display_name)s, %(child_rsg_snomed_codes)s, %(loinc_codes)s, %(snomed_codes)s, %(icd10_codes)s, %(rxnorm_codes)s)
                """
            )
            cursor.executemany(insert_query, conditions_to_insert)
            conn.commit()

            logger.info("🎉 SUCCESS: Database seeding complete!")

    except (psycopg.Error, Exception):
        logger.error(
            "❌ A critical error occurred during the seeding process.", exc_info=True
        )
        logger.error("Make sure migrations have been run prior to seeding!")
        raise


if __name__ == "__main__":
    load_dotenv(dotenv_path=ENV_PATH)
    if not (db_url := os.getenv("DB_URL")) or not (
        db_password := os.getenv("DB_PASSWORD")
    ):
        logger.critical("DB_URL and DB_PASSWORD environment variables must be set.")
    else:
        seed_database(db_url=db_url, db_password=db_password)

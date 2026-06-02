from uuid import uuid4

from app.db.code_systems.db import DbCodeSystem
from app.services.terminology import CodeSystemKey

CODE_SYSTEM_DATA = {
    "snomed": {"oid": "2.16.840.1.113883.6.96", "display_name": "SNOMED"},
    "loinc": {"oid": "2.16.840.1.113883.6.1", "display_name": "LOINC"},
    "icd10": {"oid": "2.16.840.1.113883.6.90", "display_name": "ICD-10"},
    "rxnorm": {"oid": "2.16.840.1.113883.6.88", "display_name": "RxNorm"},
    "cvx": {"oid": "2.16.840.1.113883.12.292", "display_name": "CVX"},
    "other": {"oid": "Other", "display_name": "Other"},
}


def create_mock_code_systems():
    return {
        key: DbCodeSystem(
            id=uuid4(),
            oid=system["oid"],
            display_name=system["display_name"],
            key=key,
        )
        for key, system in CODE_SYSTEM_DATA.items()
    }


def create_mock_code_system(key: CodeSystemKey):
    return create_mock_code_systems()[key]


def get_mock_allowed_system_keys():
    return create_mock_code_systems().keys()

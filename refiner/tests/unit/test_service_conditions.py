from uuid import uuid4

import pytest

from app.db.conditions.model import DbCondition
from app.services.conditions import _get_computed_name, create_condition_mapping_payload


def _make_db_condition(name: str, url: str, version: str, rsg_code: str):
    return DbCondition(
        display_name=name,
        canonical_url=url,
        version=version,
        id=(uuid4()),
        child_rsg_snomed_codes=[rsg_code],
        snomed_codes=[],
        loinc_codes=[],
        icd10_codes=[],
        rxnorm_codes=[],
        cvx_codes=[],
    )


@pytest.mark.parametrize(
    "display_name, expected",
    [
        (
            "Esophageal Atresia/Tracheoesophageal Fistula",
            "EsophagealAtresiaTracheoesophagealFistula",
        ),
        (
            "Clostridioides difficile (C. diff) infection",
            "ClostridioidesdifficileCdiffinfection",
        ),
        (
            "Nontuberculous Mycobacteria Infection, Pulmonary",
            "NontuberculousMycobacteriaInfectionPulmonary",
        ),
        ("Arboviral Disease [Other]", "ArboviralDiseaseOther"),
        ("Coal Workers’ Pneumoconiosis (CWP)", "CoalWorkersPneumoconiosisCWP"),
        ("Guillain-Barré Syndrome", "GuillainBarreSyndrome"),
        ("Trisomy 13", "Trisomy13"),
    ],
)
def test_create_condition_mapping_payload_computed_names(
    display_name: str, expected: str
):
    test_rsg = "test"
    cond = _make_db_condition(
        name=display_name,
        url="https://tes.tools.aimsplatform.org/api/fhir/ValueSet/test",
        version="4.0.0",
        rsg_code=test_rsg,
    )

    payload = create_condition_mapping_payload([cond])

    assert test_rsg in payload.mappings
    assert payload.mappings[test_rsg].canonical_url == cond.canonical_url
    assert payload.mappings[test_rsg].name == expected

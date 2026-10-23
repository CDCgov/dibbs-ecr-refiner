from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DbConditionCode:
    """
    One code a condition owns, as aggregated off `conditions_codes_temp`.

    Carries `system_id` and no system label. The label was joined in for four
    queries and read by none of them; the id stays because deduplication keys on
    `(code, display_name, system_id)`, and `codes` is `UNIQUE (system_id, code)` -- so
    that is equivalent to counting distinct `(system_id, code)` **by
    construction**. Dropping the id would make the count correct only by data
    coincidence: no condition in the corpus currently has one code string in two
    systems, but the schema permits it.

    This is what is left of `DbCode`, which was the union of three queries'
    `SELECT` lists. The other two are `DbLabeledCode` and `DbConfigurationCode`.
    """

    code: str
    display_name: str
    system_id: UUID


@dataclass(frozen=True)
class DbConfigurationCode:
    """
    One code a configuration contributes to `active.json`.

    Its system arrives **resolved to an OID** in SQL.

    `services/configurations.py` maps these to `Coding` where it merges them with the
    configuration's custom codes; the refiner never sees this type.

    `system_oid` is the literal `"Other"` for custom codes in the catch-all system;
    that is a routing key into `OID_TO_SYSTEM_KEY_MAP`, not an identifier.
    """

    code: str
    display_name: str
    system_oid: str


@dataclass(frozen=True)
class DbChildRsgCode:
    """
    A SNOMED code that names one of a condition's child RSGs, with its label.

    No system is carried: `is_child_rsg` codes are SNOMED by construction. Routes map
    these to `CodeLabel` for the client.
    """

    code: str
    display_name: str


@dataclass(frozen=True)
class DbLabeledCode:
    """
    A code with its own label and its system's label -- one row per distinct triple.

    The system is a **label**, not an OID: these rows are written to a spreadsheet
    for a person to read, never matched against a document.
    """

    code: str
    display_name: str
    system_display_name: str

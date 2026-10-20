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
    `SELECT` lists. The other two now take `CodeExportRow` and `Coding` from
    `core/models/terminology.py`.
    """

    code: str
    display_name: str
    system_id: UUID

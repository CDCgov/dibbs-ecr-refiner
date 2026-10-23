from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DbCodeSystem:
    """
    One row of the `systems` table: a code system the app can store codes in.

    Read as-is by every internal consumer -- `services` resolves a custom code's
    `system_id` to the OID the refiner matches on, and validates CSV imports against
    `display_name`. Routes map it to their own wire models.

    `oid` is the literal `"Other"` on exactly one row -- the catch-all for custom
    codes with no standard system. That is a routing key into
    `OID_TO_SYSTEM_KEY_MAP`, not an identifier; see the note on `Coding`.
    """

    id: UUID
    key: str
    display_name: str
    oid: str

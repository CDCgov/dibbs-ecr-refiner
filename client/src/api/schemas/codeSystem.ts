
/**
 * One row of the `systems` table: a code system the app can store codes in.
 *
 * Carries no `Db` prefix, for the same reason as `CodeSetSummary`. It is a row out
 * of Postgres **and** it is generated to the client (the custom-code CSV import
 * needs the list of systems a user may pick), which rule 3 says cannot both be
 * true of a `Db*` model. ADR 0016 §2.4 called this the hardest case; dropping the
 * prefix follows the `ConfiguredSection` precedent the ADR blesses for anything
 * belonging to no single boundary.
 *
 * `oid` is the literal `"Other"` on exactly one row -- the catch-all for custom
 * codes with no standard system. That is a routing key into
 * `OID_TO_SYSTEM_KEY_MAP`, not an identifier; see the note on `Coding`.
 */
export interface CodeSystem {
  id: string;
  key: string;
  display_name: string;
  oid: string;
}

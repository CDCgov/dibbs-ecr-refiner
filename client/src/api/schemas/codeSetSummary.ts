
/**
 * One code set a configuration includes, with how many codes it contributes.
 *
 * "Code set" is what the UI calls a condition associated to a configuration, so the
 * identifier follows rule 7's settled `code_set` spelling.
 *
 * Carries no `Db` prefix on purpose. Rule 3 reserves that for a row or projection
 * out of Postgres that is **never** generated to the client, and this is both -- a
 * `class_row` projection that ships on `GetConfigurationResponse.code_sets`. ADR
 * 0016 §2.4 flagged the same contradiction for `DbCodeSystem`; dropping the prefix
 * follows the `ConfiguredSection` precedent, which the ADR blesses for anything
 * belonging to no boundary.
 */
export interface CodeSetSummary {
  condition_id: string;
  display_name: string;
  code_count: number;
}

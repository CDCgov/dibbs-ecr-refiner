
/**
 * Code count information to return to the client.
 *
 * Field-identical to `DbCodeResultCountMetadata` now that both follow
 * `<thing>_count`. The mapping below was already a pure rename; collapsing the two
 * models is an E1 question (a db shape reaching the browser), not a naming one.
 */
export interface CodeCountsResponse {
  code_count: number;
  code_set_count: number;
  excluded_code_count: number;
  custom_code_count: number;
  primary_condition_rctc_count: number;
}

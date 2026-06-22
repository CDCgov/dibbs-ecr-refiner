
/**
 * DB model for code stored in the codes table.
 */
export interface DbCode {
  code: string;
  display: string;
  version: string;
  system_id: string;
}

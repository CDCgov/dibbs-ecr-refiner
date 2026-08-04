import type { DbCodeResult } from './dbCodeResult';

/**
 * Codes and metadata to return to the client.
 */
export interface CodesResponse {
  codes: DbCodeResult[];
  total_code_count: number;
  total_code_sets_count: number;
  total_excluded_codes_count: number;
}


/**
 * A changed condition within a TES update.
 */
export interface TesDiffResponse {
  canonical_url: string;
  display_name: string;
  added_code_total: number;
  removed_code_total: number;
  is_new: boolean;
}

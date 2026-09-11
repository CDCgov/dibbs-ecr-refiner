
/**
 * A condition within a TES diff, with details for the diff page to display.
 */
export interface TesDiffConditionDetails {
  canonical_url: string;
  display_name: string;
  added_code_total: number;
  removed_code_total: number;
  is_new: boolean;
}

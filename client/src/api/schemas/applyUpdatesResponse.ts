
/**
 * Response model for applying TES updates to configurations.
 */
export interface ApplyUpdatesResponse {
  total_processed: number;
  drafts_updated: number;
  drafts_created: number;
  updated_configuration_ids: string[];
  created_configuration_ids: string[];
}

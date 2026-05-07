import type { Condition } from './condition';

/**
 * Model for the response when uploading a document in the testing suite.
 */
export interface IndependentTestUploadResponse {
  message: string;
  conditions_without_matching_configs: string[];
  conditions_without_active_configs: string[];
  refined_conditions_found: number;
  refined_conditions: Condition[];
  unrefined_eicr: string;
  refined_download_key: string;
}

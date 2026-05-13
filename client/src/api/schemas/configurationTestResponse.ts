import type { Condition } from './condition';

/**
 * Model to represent the response provided to the client when in-line testing is run.
 */
export interface ConfigurationTestResponse {
  original_eicr: string;
  refined_download_key: string;
  condition: Condition;
}

import type { CustomCodeResponse } from './customCodeResponse';
import type { DbTotalConditionCodeCount } from './dbTotalConditionCodeCount';

/**
 * Configuration response for custom code operations (add/edit/delete).
 */
export interface ConfigurationCustomCodeResponse {
  id: string;
  display_name: string;
  code_sets: DbTotalConditionCodeCount[];
  custom_codes: CustomCodeResponse[];
}

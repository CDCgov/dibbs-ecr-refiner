import type { ConditionEntry } from './conditionEntry';

/**
 * Response from adding a code set to a config.
 */
export interface AssociateCodesetResponse {
  id: string;
  included_conditions: ConditionEntry[];
  condition_name: string;
}

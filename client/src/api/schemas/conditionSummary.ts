import type { Coding } from './coding';

/**
 * High-level information for a condition.
 */
export interface ConditionSummary {
  id: string;
  display_name: string;
  rsg_codes: Coding[];
}

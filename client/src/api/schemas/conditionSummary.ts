import type { CodedConcept } from './codedConcept';

/**
 * High-level information for a condition.
 */
export interface ConditionSummary {
  id: string;
  display_name: string;
  rsg_codes: CodedConcept[];
}

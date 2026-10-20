import type { CompletenessStatus } from './completenessStatus';

/**
 * Condition response model.
 *
 * Carries no code list on purpose: a condition's codes are paged through
 * `configurations/{id}/codes`, and code systems through `code_systems`. Returning
 * them whole here meant tens of thousands of rows per request that no caller read.
 */
export interface GetConditionResponse {
  id: string;
  display_name: string;
  completeness_status: CompletenessStatus;
}

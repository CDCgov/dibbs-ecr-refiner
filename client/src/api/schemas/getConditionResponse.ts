import type { CompletenessStatus } from './completenessStatus';
import type { DbCodeSystem } from './dbCodeSystem';
import type { GetConditionCode } from './getConditionCode';

/**
 * Condition response model.
 */
export interface GetConditionResponse {
  id: string;
  display_name: string;
  completeness_status: CompletenessStatus;
  codes: GetConditionCode[];
  systems: DbCodeSystem[];
}

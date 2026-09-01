import type { CodeSystemsReponse } from './codeSystemsReponse';
import type { CompletenessStatus } from './completenessStatus';
import type { DbCode } from './dbCode';

/**
 * Condition response model.
 */
export interface GetConditionResponse {
  id: string;
  display_name: string;
  completeness_status: CompletenessStatus;
  codes: DbCode[];
  systems: CodeSystemsReponse[];
}

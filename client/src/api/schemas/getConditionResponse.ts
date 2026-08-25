import type { AppDbConditionsModelCodeResponse } from './appDbConditionsModelCodeResponse';
import type { CodeSystemsReponse } from './codeSystemsReponse';
import type { CompletenessStatus } from './completenessStatus';

/**
 * Condition response model.
 */
export interface GetConditionResponse {
  id: string;
  display_name: string;
  completeness_status: CompletenessStatus;
  codes: AppDbConditionsModelCodeResponse[];
  systems: CodeSystemsReponse[];
}

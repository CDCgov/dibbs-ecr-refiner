import type { CodeLabel } from './codeLabel';

/**
 * Conditions response model.
 */
export interface GetConditionsResponse {
  id: string;
  display_name: string;
  rsg_codes: CodeLabel[];
}

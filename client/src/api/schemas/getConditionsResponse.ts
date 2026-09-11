import type { CodedConcept } from './codedConcept';

/**
 * Conditions response model.
 */
export interface GetConditionsResponse {
  id: string;
  display_name: string;
  rsg_codes: CodedConcept[];
}

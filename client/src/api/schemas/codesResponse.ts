import type { CodeResponse } from './codeResponse';
import type { CodesLimitResponse } from './codesLimitResponse';

/**
 * Codes and metadata to return to the client.
 */
export interface CodesResponse {
  next_cursor: string | null;
  codes: CodeResponse[];
  codes_limit: CodesLimitResponse;
}

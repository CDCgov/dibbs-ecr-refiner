import type { CodeResponse } from './codeResponse';

/**
 * Codes and metadata to return to the client.
 */
export interface CodesResponse {
  next_cursor: string | null;
  codes: CodeResponse[];
}

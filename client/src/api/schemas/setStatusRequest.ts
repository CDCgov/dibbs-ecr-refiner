import type { CodeStatus } from './codeStatus';

/**
 * Request body class for code status change.
 */
export interface SetStatusRequest {
  code_ids: string[];
  status: CodeStatus;
}

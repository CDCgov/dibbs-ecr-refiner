import type { CodeStatus } from './codeStatus';

export interface SetStatusRequest {
  code_ids: string[];
  status: CodeStatus;
}

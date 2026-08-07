import type { CodeResponseStatus } from './codeResponseStatus';

/**
 * Code object to return to the client.
 */
export interface CodeResponse {
  id: string;
  condition_id: string | null;
  source: string;
  code: string;
  description: string;
  system_id: string;
  system_name: string;
  status: CodeResponseStatus;
  is_custom: boolean;
}

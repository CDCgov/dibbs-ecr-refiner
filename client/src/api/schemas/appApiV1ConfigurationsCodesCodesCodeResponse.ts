import type { AppApiV1ConfigurationsCodesCodesCodeResponseStatus } from './appApiV1ConfigurationsCodesCodesCodeResponseStatus';

/**
 * Code object to return to the client.
 */
export interface AppApiV1ConfigurationsCodesCodesCodeResponse {
  id: string;
  condition_id: string | null;
  source: string[];
  code: string;
  description: string;
  system_id: string;
  system_name: string;
  status: AppApiV1ConfigurationsCodesCodesCodeResponseStatus;
  is_custom: boolean;
}

import type { AppApiV1ConfigurationsCodesCodesCodeResponse } from './appApiV1ConfigurationsCodesCodesCodeResponse';

/**
 * Codes and metadata to return to the client.
 */
export interface CodesResponse {
  next_cursor: string | null;
  codes: AppApiV1ConfigurationsCodesCodesCodeResponse[];
}

import type { TesUpdate } from './tesUpdate';

/**
 * Response needed for the audit log page.
 */
export interface TesResponse {
  tes_updates: TesUpdate[];
}

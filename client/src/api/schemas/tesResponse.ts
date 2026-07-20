import type { TesUpdate } from './tesUpdate';

/**
 * Response needed for the TES updates page.
 */
export interface TesResponse {
  tes_updates: TesUpdate[];
}

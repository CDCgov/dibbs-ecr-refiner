import type { TesConfigToUpdate } from './tesConfigToUpdate';

/**
 * The response needed for rendering of the TES update configuration page.
 */
export interface TesConfigsToUpdateResponse {
  existing_drafts: TesConfigToUpdate[];
  drafts_to_create: TesConfigToUpdate[];
}

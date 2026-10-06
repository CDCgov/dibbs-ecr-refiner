
/**
 * A configuration to update with new TES codes.
 */
export interface TesConfigToUpdate {
  configuration_id: string;
  configuration_name: string;
  codesets_to_update: string[];
  configuration_tes_version: string;
}

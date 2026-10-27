import type { ConfigurationStatus } from './configurationStatus';

/**
 * Model to represent individual discovered configurations.
 */
export interface DiscoveredConfigurationVersion {
  id: string;
  version: number;
  status: ConfigurationStatus;
}

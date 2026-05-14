import type { DbConfigurationStatus } from './dbConfigurationStatus';

/**
 * Model to represent individual discovered configurations.
 */
export interface DiscoveredConfigurationVersion {
  id: string;
  version: number;
  status: DbConfigurationStatus;
}

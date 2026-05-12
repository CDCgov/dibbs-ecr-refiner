import type { DiscoveredConfigurationVersion } from './discoveredConfigurationVersion';

/**
 * Model to represent a group of discovered configurations.
 */
export interface DiscoveredConfigurationGroup {
  name: string;
  versions: DiscoveredConfigurationVersion[];
}

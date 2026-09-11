import type { DiscoveredConfigurationVersion } from './discoveredConfigurationVersion';

/**
 * Model to represent a set of discovered configurations.
 */
export interface DiscoveredConfigurationSet {
  name: string;
  condition_id: string;
  versions: DiscoveredConfigurationVersion[];
}

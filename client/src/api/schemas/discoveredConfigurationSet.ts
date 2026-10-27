import type { DiscoveredConfigurationVersion } from './discoveredConfigurationVersion';

/**
 * Model to represent a set of discovered configurations.
 */
export interface DiscoveredConfigurationSet {
  display_name: string;
  condition_id: string;
  versions: DiscoveredConfigurationVersion[];
}

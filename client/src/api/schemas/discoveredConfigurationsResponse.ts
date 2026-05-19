import type { DiscoveredConfigurationSet } from './discoveredConfigurationSet';

/**
 * Model to represent the sets of discovered configurations to return to the client.
 */
export interface DiscoveredConfigurationsResponse {
  sets: DiscoveredConfigurationSet[];
}

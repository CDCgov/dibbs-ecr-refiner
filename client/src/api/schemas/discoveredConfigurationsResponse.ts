import type { DiscoveredConfigurationGroup } from './discoveredConfigurationGroup';

/**
 * Model to represent the groups of discovered configurations to return to the client.
 */
export interface DiscoveredConfigurationsResponse {
  groups: DiscoveredConfigurationGroup[];
}

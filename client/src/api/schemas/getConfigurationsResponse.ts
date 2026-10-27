import type { ConfigurationStatus } from './configurationStatus';

/**
 * Model for a user-defined configuration.
 */
export interface GetConfigurationsResponse {
  id: string;
  display_name: string;
  status: ConfigurationStatus;
}

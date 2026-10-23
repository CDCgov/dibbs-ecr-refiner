import type { ConfigurationStatus } from './configurationStatus';

/**
 * Response model for updating the status a configuration.
 */
export interface ConfigurationStatusUpdateResponse {
  configuration_id: string;
  status: ConfigurationStatus;
}

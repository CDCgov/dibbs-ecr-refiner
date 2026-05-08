import type { DbConfigurationStatus } from './dbConfigurationStatus';

/**
 * Response model for updating the status a configuration.
 */
export interface ConfigurationStatusUpdateResponse {
  configuration_id: string;
  status: DbConfigurationStatus;
}

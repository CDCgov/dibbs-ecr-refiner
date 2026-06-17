import type { Coding } from './coding';
import type { DbConfigurationStatus } from './dbConfigurationStatus';

/**
 * Model for a user-defined configuration.
 */
export interface GetConfigurationsResponse {
  id: string;
  name: string;
  status: DbConfigurationStatus;
  rsg_codes: Coding[];
}

import type { DbCoding } from './dbCoding';
import type { DbConfigurationStatus } from './dbConfigurationStatus';

/**
 * Model for a user-defined configuration.
 */
export interface GetConfigurationsResponse {
  id: string;
  name: string;
  status: DbConfigurationStatus;
  rsg_codes: DbCoding[];
}

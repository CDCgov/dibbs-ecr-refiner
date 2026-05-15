import type { DbConfigurationStatus } from './dbConfigurationStatus';

/**
 * Model representing a version of a configuration.
 */
export interface GetConfigurationResponseVersion {
  id: string;
  version: number;
  condition_canonical_url: string;
  status: DbConfigurationStatus;
  created_at: string;
  created_by: string;
  last_activated_at: string | null;
  last_activated_by: string | null;
}

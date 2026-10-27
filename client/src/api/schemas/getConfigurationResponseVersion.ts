import type { ConfigurationStatus } from './configurationStatus';

/**
 * Model representing a version of a configuration.
 */
export interface GetConfigurationResponseVersion {
  id: string;
  version: number;
  condition_canonical_url: string;
  status: ConfigurationStatus;
  created_at: string;
  created_by: string;
  last_activated_at: string | null;
  last_activated_by: string | null;
}

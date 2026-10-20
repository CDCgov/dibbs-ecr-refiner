import type { ConfigurationCodeStatus } from './configurationCodeStatus';
import type { ConfigurationCodeStatusLabel } from './configurationCodeStatusLabel';

/**
 * Model to represent a status filter option.
 */
export interface StatusFilterOption {
  display_name: ConfigurationCodeStatusLabel;
  status: ConfigurationCodeStatus;
  code_count: number;
}

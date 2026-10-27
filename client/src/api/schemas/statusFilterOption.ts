import type { ConfigurationCodeStatus } from './configurationCodeStatus';
import type { ConfigurationCodeStatusLabel } from './configurationCodeStatusLabel';

/**
 * An included/excluded status the client can filter by.
 */
export interface StatusFilterOption {
  display_name: ConfigurationCodeStatusLabel;
  status: ConfigurationCodeStatus;
  code_count: number;
}

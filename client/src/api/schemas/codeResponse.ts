import type { ConfigurationCodeStatusLabel } from './configurationCodeStatusLabel';

/**
 * Code object to return to the client.
 */
export interface CodeResponse {
  id: string;
  condition_id: string | null;
  source: string[];
  code: string;
  description: string;
  system_id: string;
  system_name: string;
  status: ConfigurationCodeStatusLabel;
  is_custom: boolean;
  is_trigger_code: boolean;
}

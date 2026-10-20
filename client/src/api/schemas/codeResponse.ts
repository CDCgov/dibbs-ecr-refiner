import type { ConfigurationCodeStatusLabel } from './configurationCodeStatusLabel';

/**
 * Code object to return to the client.
 */
export interface CodeResponse {
  id: string;
  condition_id: string | null;
  source_display_names: string[];
  code: string;
  display_name: string;
  system_id: string;
  system_display_name: string;
  status: ConfigurationCodeStatusLabel;
  is_custom: boolean;
  is_trigger_code: boolean;
}

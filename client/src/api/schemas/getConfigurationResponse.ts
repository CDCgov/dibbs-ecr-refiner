import type { CodeLabel } from './codeLabel';
import type { CodeSetSummary } from './codeSetSummary';
import type { ConfigurationStatus } from './configurationStatus';
import type { ConfiguredSection } from './configuredSection';
import type { CustomCodeResponse } from './customCodeResponse';
import type { GetConfigurationResponseVersion } from './getConfigurationResponseVersion';
import type { IncludedCondition } from './includedCondition';
import type { LockedByUser } from './lockedByUser';

/**
 * Model for a configuration response.
 */
export interface GetConfigurationResponse {
  id: string;
  draft_id: string | null;
  is_draft: boolean;
  condition_id: string;
  condition_canonical_url: string;
  display_name: string;
  status: ConfigurationStatus;
  code_sets: CodeSetSummary[];
  included_conditions: IncludedCondition[];
  custom_codes: CustomCodeResponse[];
  section_processing: ConfiguredSection[];
  all_versions: GetConfigurationResponseVersion[];
  rsg_codes: CodeLabel[];
  version: number;
  active_configuration_id: string | null;
  active_version: number | null;
  latest_version: number;
  is_locked: boolean;
  locked_by: LockedByUser | null;
}

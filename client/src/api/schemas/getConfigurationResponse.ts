import type { DbConfigurationCustomCode } from './dbConfigurationCustomCode';
import type { DbConfigurationSectionProcessing } from './dbConfigurationSectionProcessing';
import type { DbConfigurationStatus } from './dbConfigurationStatus';
import type { DbTotalConditionCodeCount } from './dbTotalConditionCodeCount';
import type { GetConfigurationResponseCodeSystems } from './getConfigurationResponseCodeSystems';
import type { GetConfigurationResponseVersion } from './getConfigurationResponseVersion';
import type { IncludedCondition } from './includedCondition';
import type { LockedByUser } from './lockedByUser';

/**
 * Model for a configration response.
 */
export interface GetConfigurationResponse {
  id: string;
  draft_id: string | null;
  is_draft: boolean;
  condition_id: string;
  condition_canonical_url: string;
  display_name: string;
  status: DbConfigurationStatus;
  code_sets: DbTotalConditionCodeCount[];
  included_conditions: IncludedCondition[];
  custom_codes: DbConfigurationCustomCode[];
  section_processing: DbConfigurationSectionProcessing[];
  all_versions: GetConfigurationResponseVersion[];
  version: number;
  active_configuration_id: string | null;
  active_version: number | null;
  latest_version: number;
  is_locked: boolean;
  locked_by: LockedByUser | null;
  code_systems: GetConfigurationResponseCodeSystems;
}

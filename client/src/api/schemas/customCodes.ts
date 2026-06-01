import type { CustomCodesCodeSystems } from './customCodesCodeSystems';
import type { DbConfigurationCustomCode } from './dbConfigurationCustomCode';

/**
 * Model for custom codes response, with systems bundled alongside codes for frontend display.
 */
export interface CustomCodes {
  codes: DbConfigurationCustomCode[];
  code_systems: CustomCodesCodeSystems;
}

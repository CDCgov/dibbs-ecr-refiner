import type { DbConfigurationCustomCode } from './dbConfigurationCustomCode';
import type { IndexedCodeSystem } from './indexedCodeSystem';

/**
 * Model for custom codes response, with systems bundled alongside codes for frontend display.
 */
export interface CustomCodes {
  codes: DbConfigurationCustomCode[];
  code_systems: IndexedCodeSystem;
}

import type { CustomCodesSystems } from './customCodesSystems';
import type { DbConfigurationCustomCode } from './dbConfigurationCustomCode';

/**
 * Model for custom codes response, with systems bundled alongside codes for frontend display.
 */
export interface CustomCodes {
  codes: DbConfigurationCustomCode[];
  systems: CustomCodesSystems;
}

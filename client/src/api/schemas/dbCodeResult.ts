import type { DbCodeResultStatus } from './dbCodeResultStatus';

/**
 * Result from query.
 */
export interface DbCodeResult {
  id: string;
  condition_id: string;
  source: string;
  code: string;
  description: string;
  system_id: string;
  system_name: string;
  status: DbCodeResultStatus;
}

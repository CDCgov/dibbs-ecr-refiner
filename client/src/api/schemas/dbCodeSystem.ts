import type { CodeSystemKey } from './codeSystemKey';

/**
 * A code system row from the `systems` table.
 */
export interface DbCodeSystem {
  id: string;
  key: CodeSystemKey;
  display_name: string;
  oid: string;
}

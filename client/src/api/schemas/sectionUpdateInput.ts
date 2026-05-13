import type { DbSectionAction } from './dbSectionAction';

/**
 * Request body for modifying a section.
 */
export interface SectionUpdateInput {
  include?: boolean | null;
  narrative?: boolean | null;
  action?: DbSectionAction | null;
  name?: string | null;
  current_code: string;
  new_code?: string | null;
}

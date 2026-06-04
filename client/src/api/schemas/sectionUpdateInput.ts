import type { DbSectionAction } from './dbSectionAction';
import type { DbSectionNarrative } from './dbSectionNarrative';

/**
 * Input model for updating a section's processing instructions.
 */
export interface SectionUpdateInput {
  include?: boolean | null;
  narrative?: DbSectionNarrative | null;
  action?: DbSectionAction | null;
  name?: string | null;
  current_code: string;
  new_code?: string | null;
}

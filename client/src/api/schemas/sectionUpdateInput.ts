import type { DbNarrativeAction } from './dbNarrativeAction';
import type { DbSectionAction } from './dbSectionAction';

/**
 * Input model for updating a section's processing instructions.
 */
export interface SectionUpdateInput {
  include?: boolean | null;
  narrative?: DbNarrativeAction | null;
  action?: DbSectionAction | null;
  name?: string | null;
  current_code: string;
  new_code?: string | null;
}

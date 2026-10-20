import type { NarrativeAction } from './narrativeAction';
import type { SectionAction } from './sectionAction';

/**
 * Input model for updating a section's processing instructions.
 */
export interface SectionUpdateInput {
  include?: boolean | null;
  narrative?: NarrativeAction | null;
  action?: SectionAction | null;
  display_name?: string | null;
  current_code: string;
  new_code?: string | null;
}

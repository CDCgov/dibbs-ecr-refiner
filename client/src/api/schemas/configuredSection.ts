import type { NarrativeAction } from './narrativeAction';
import type { SectionAction } from './sectionAction';
import type { SectionType } from './sectionType';

/**
 * Section Processing instructions for a Configuration.
 *
 * `display_name` is the section's label.
 * `code` is the LOINC code for the section.
 * `versions` is a list of versions this section appears in.
 * `section_type` is an indicator as to how the section was created.
 *
 * Field order is carried over from the base class this used to inherit, so
 * that nothing downstream shifts: `asdict(DbConfiguration)` recurses into
 * `section_processing` for the structured log payloads in
 * `services/testing.py`, and that key order follows declaration order here.
 */
export interface ConfiguredSection {
  include: boolean;
  narrative: NarrativeAction;
  action: SectionAction;
  display_name: string;
  code: string;
  versions: string[];
  section_type: SectionType;
}

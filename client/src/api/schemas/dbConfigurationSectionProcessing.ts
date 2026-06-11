import type { DbNarrativeAction } from './dbNarrativeAction';
import type { DbSectionAction } from './dbSectionAction';
import type { DbSectionType } from './dbSectionType';

/**
 * Section Processing instructions for a Configuration.

`name` is the section's name.
`code` is the LOINC code for the section.
`versions` is a list of versions this section appears in.
`section_type` is an indicator as to how the section was created.
 */
export interface DbConfigurationSectionProcessing {
  include: boolean;
  narrative: DbNarrativeAction;
  action: DbSectionAction;
  name: string;
  code: string;
  versions: string[];
  section_type: DbSectionType;
}

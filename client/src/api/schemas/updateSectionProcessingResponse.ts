import type { DisabledSection } from './disabledSection';
import type { NarrativeOnlySection } from './narrativeOnlySection';

/**
 * Section with information for a custom section update.
 */
export interface UpdateSectionProcessingResponse {
  section_updated_code: string;
  disabled_section: DisabledSection[];
  narrative_only_section: NarrativeOnlySection[];
}

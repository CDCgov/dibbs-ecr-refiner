import type { CodedDataLabels } from './codedDataLabels';
import type { DisabledSection } from './disabledSection';
import type { NarrativeDataLabels } from './narrativeDataLabels';
import type { NarrativeOnlySection } from './narrativeOnlySection';
import type { ReconstructableSection } from './reconstructableSection';

/**
 * Section with information for a custom section update.
 */
export interface UpdateSectionProcessingResponse {
  section_updated_code: string;
  disabled_section: DisabledSection[];
  narrative_only_section: NarrativeOnlySection[];
  reconstructable_section: ReconstructableSection[];
  narrative_data_labels: NarrativeDataLabels;
  coded_data_labels: CodedDataLabels;
}

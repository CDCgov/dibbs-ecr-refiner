import { Select } from '@components/Select';
import { useSectionUpdater } from './useSectionUpdater';
import {
  DbNarrativeAction,
  DbConfigurationSectionProcessing,
} from '../../../../api/schemas';

// TODO: Add "Reconstruct" option once backend `narrative` field supports 3-value enum
// (retain | remove | refine). Currently limited to boolean (true = retain, false = remove).

interface NarrativeSelectProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  disabled: boolean;
}

export function NarrativeSelect({
  configurationId,
  currentSection,
  disabled,
}: NarrativeSelectProps) {
  const updateSection = useSectionUpdater(configurationId);

  return (
    <div className="flex-start flex">
      <Select
        disabled={disabled}
        value={currentSection.narrative}
        onChange={(e) => {
          updateSection(currentSection, {
            narrative: e.target.value as DbNarrativeAction,
          });
        }}
        aria-label={`Narrative data handling for ${currentSection.name} section`}
        className="min-w-38"
      >
        <option value="retain">Keep original</option>
        <option value="remove">Remove</option>
      </Select>
    </div>
  );
}

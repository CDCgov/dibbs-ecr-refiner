import { Select } from '@components/Select';
import { Field } from '@components/Field';
import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { DbSectionNarrative } from '../../../../api/schemas/dbSectionNarrative';
import { useSectionUpdater } from './useSectionUpdater';

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
    <Field className="flex items-center gap-3">
      <Select
        disabled={disabled}
        value={currentSection.narrative ? 'retain' : 'remove'}
        onChange={(e) => {
          updateSection(currentSection, {
            narrative:
              e.target.value === 'retain'
                ? DbSectionNarrative.retain
                : DbSectionNarrative.remove,
          });
        }}
        aria-label={`Narrative data handling for ${currentSection.name} section`}
        className="min-w-38"
      >
        <option value="retain">Keep original</option>
        <option value="remove">Remove</option>
      </Select>
    </Field>
  );
}

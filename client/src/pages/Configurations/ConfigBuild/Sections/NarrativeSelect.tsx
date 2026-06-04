import { Select } from '@components/Select';
import { Field } from '@components/Field';
import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { DbSectionAction, DbSectionNarrative } from '../../../../api/schemas';
import { useSectionUpdater } from './useSectionUpdater';

// TODO: Actual reconstruction logic is not yet implemented in backend.
// When narrative="refine" is selected, the backend currently treats it as "remove".
// See refiner/app/services/ecr/refine.py for the TODO comment.

// TODO: Audit the existing frontend architecture in `client/src/pages` to identify
// bottlenecks for forthcoming Refiner 2.0 designs

interface NarrativeSelectProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  disabled: boolean;
  isNarrativeOnly: boolean;
  codedDataAction: DbSectionAction;
  onClearError: () => void;
}

export function NarrativeSelect({
  configurationId,
  currentSection,
  disabled,
  isNarrativeOnly,
  codedDataAction,
  onClearError,
}: NarrativeSelectProps) {
  const updateSection = useSectionUpdater(configurationId);

  return (
    <Field className="flex items-center gap-3">
      <Select
        disabled={disabled}
        value={currentSection.narrative}
        onChange={(e) => {
          onClearError();
          updateSection(currentSection, {
            narrative: e.target.value as DbSectionNarrative,
          });
        }}
        aria-label={`Narrative data handling for ${currentSection.name} section`}
        className="min-w-44"
      >
        <option value="retain">Keep original</option>
        {!isNarrativeOnly && (
          <option value="refine" disabled={codedDataAction === 'retain'}>
            Reconstruct
          </option>
        )}
        <option value="remove">Exclude</option>
      </Select>
    </Field>
  );
}

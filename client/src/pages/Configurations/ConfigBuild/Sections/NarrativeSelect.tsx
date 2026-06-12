import { Select } from '@components/Select';
import { Field } from '@components/Field';
import { useSectionUpdater } from './useSectionUpdater';
import {
  DbSectionAction,
  DbNarrativeAction,
  DbConfigurationSectionProcessing,
} from '../../../../api/schemas';

// TODO: Actual reconstruction logic is not yet implemented in backend. When
// narrative="reconstruct" is selected, the backend currently treats it as
// "remove".
// See refiner/app/services/ecr/refine.py for the `TODO:`

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
            narrative: e.target.value as DbNarrativeAction,
          });
        }}
        aria-label={`Narrative data handling for ${currentSection.name} section`}
        className="min-w-38"
      >
        <option value="retain">Keep original</option>
        {!isNarrativeOnly && (
          <option value="reconstruct" disabled={codedDataAction === 'retain'}>
            Reconstruct
          </option>
        )}
        <option value="remove">Exclude</option>
      </Select>
    </Field>
  );
}

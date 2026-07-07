import { Select } from '@components/Select';
import { useSectionUpdater } from './useSectionUpdater';
import { useSectionError } from './useSectionError';
import {
  DbSectionAction,
  DbNarrativeAction,
  DbConfigurationSectionProcessing,
  NarrativeDataLabelsValue,
} from '../../../../api/schemas';

// TODO: Audit the existing frontend architecture in `client/src/pages` to identify
// bottlenecks for forthcoming Refiner 2.0 designs

interface NarrativeSelectProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  disabled: boolean;
  isNarrativeOnly: boolean;
  isReconstructable: boolean;
  codedDataAction: DbSectionAction;
}

export function NarrativeSelect({
  configurationId,
  currentSection,
  disabled,
  isNarrativeOnly,
  isReconstructable,
  codedDataAction,
}: NarrativeSelectProps) {
  const updateSection = useSectionUpdater(configurationId);
  const { clearError } = useSectionError();

  return (
    <div className="flex-start flex">
      <Select
        disabled={disabled}
        value={currentSection.narrative}
        onChange={(e) => {
          clearError();
          updateSection(currentSection, {
            narrative: e.target.value as DbNarrativeAction,
          });
        }}
        aria-label={`Narrative data handling for ${currentSection.name} section`}
        className="min-w-38"
      >
        <option value="retain">{NarrativeDataLabelsValue.retain}</option>
        {!isNarrativeOnly && isReconstructable && (
          <option value="reconstruct" disabled={codedDataAction === 'retain'}>
            {NarrativeDataLabelsValue.reconstruct}
          </option>
        )}
        <option value="remove">{NarrativeDataLabelsValue.remove}</option>
      </Select>
    </div>
  );
}

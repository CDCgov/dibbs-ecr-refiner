import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import {
  CodedDataLabelsValue,
  DbSectionAction,
  DisabledSection,
  GetConfigurationResponse,
  NarrativeOnlySection,
  ReconstructableSection,
} from '../../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useDeleteCustomSection,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Button } from '@components/Button';
import { CustomSectionModal } from './CustomSectionModal';
import { CustomSectionBadge } from './CustomSectionBadge';
import { Switch } from '@components/Switch';
import { NarrativeSelect } from './NarrativeSelect';
import { useSectionUpdater } from './useSectionUpdater';
import { SectionErrorProvider } from './SectionErrorProvider';
import { useSectionError } from './useSectionError';
import classNames from 'classnames';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Tooltip } from '@components/Tooltip';
import { KeepOnMatchModal } from './KeepOnMatchModal';
import { InfoIcon } from '@components/Icons/InfoIcon';

export interface SectionModalState {
  isOpen: boolean;
  selectedSection: DbConfigurationSectionProcessing | null;
}

interface SectionsProps {
  configuration: GetConfigurationResponse;
  disabled: boolean;
  modalState: SectionModalState;
  setModalState: React.Dispatch<React.SetStateAction<SectionModalState>>;
}

export function Sections({
  configuration,
  disabled,
  modalState,
  setModalState,
}: SectionsProps) {
  const [isInfoOpen, setIsInfoOpen] = useState(false);

  // these LOINC codes are sourced from the server (see refiner/app/services/ecr/policy.py):
  //   - disabled_sections: sections that are always retained by the refiner regardless of
  //     configuration, so the user shouldn't be able to toggle them in the UI
  //   - narrative_only_sections: sections with no entry match rules in the eICR spec, so
  //     "refine" is meaningless for them — we surface "Not applicable" instead of a switch
  const disabledSections = Object.values(DisabledSection);
  const isDisabledSection = (s: string): s is DisabledSection =>
    disabledSections.some((v) => (v as string) === s);

  const narrativeOnlySections = Object.values(NarrativeOnlySection);
  const isNarrativeSection = (s: string): s is NarrativeOnlySection =>
    narrativeOnlySections.some((v) => (v as string) === s);

  const reconstructableSections = Object.values(ReconstructableSection);
  const isReconstructableSection = (s: string): s is ReconstructableSection =>
    reconstructableSections.some((v) => (v as string) === s);

  const onSelectedSection = (section: DbConfigurationSectionProcessing) => {
    setModalState({ isOpen: true, selectedSection: section });
  };

  const resetModal = () => {
    setModalState((prev) => ({ ...prev, selectedSection: null }));
  };

  return (
    <SectionErrorProvider>
      <section className="flex max-h-150 min-h-0 w-full flex-1 flex-col">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <CustomSectionModal
              isOpen={modalState.isOpen}
              setIsOpen={(isOpen) =>
                setModalState((prev) => ({ ...prev, isOpen: !!isOpen }))
              }
              configurationId={configuration.id}
              initialSection={
                modalState.selectedSection
                  ? {
                      name: modalState.selectedSection.name,
                      currentCode: modalState.selectedSection.code,
                    }
                  : null
              }
              onClose={resetModal}
            />
            <KeepOnMatchModal isOpen={isInfoOpen} setIsOpen={setIsInfoOpen} />
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-scroll">
          {/* TODO: Revisit table layout for Refiner 2.0 UI migration. Evaluate
              whether a virtualized list is appropriate for large section counts.
              */}
          <table className="w-full table-fixed">
            <thead className="bg-page-bg border-gray-cool-70 sticky top-0 z-sticky border-b-2">
              <tr className="text-gray-cool-60">
                <th scope="col" className="w-20 py-3">
                  <div className="flex justify-center gap-1">
                    <span>Include</span>
                    <Tooltip
                      position="right"
                      label="Turn a section on to include it in the refined eICR, or off to leave it out entirely."
                    />
                  </div>
                </th>
                <th scope="col" className="w-70 text-left">
                  Section name
                </th>
                <th scope="col" className="w-60">
                  <div className="flex justify-center gap-1">
                    <span>Coded data</span>
                    <Tooltip
                      position="left"
                      label="Turn on Refine to filter this section's coded entries down to the codes in your configuration. Off keeps all coded data."
                    />
                  </div>
                </th>
                <th scope="col" className="w-40">
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1">
                      <span>Narrative data</span>
                      <Button
                        variant="unstyled"
                        type="button"
                        onClick={() => setIsInfoOpen(true)}
                        className="inline-flex cursor-pointer rounded-sm focus:outline-2 focus:outline-offset-2 focus:outline-blue-600"
                      >
                        <span aria-hidden>
                          <InfoIcon />
                        </span>
                        <span className="sr-only">More information</span>
                      </Button>
                    </div>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-gray-cool-20 divide-y">
              {configuration.section_processing.map((section) => (
                <tr key={section.code} className="text-gray-cool-90">
                  <td>
                    <div className="flex justify-center p-8">
                      <IncludeSwitch
                        configurationId={configuration.id}
                        currentSection={section}
                        sections={configuration.section_processing}
                        disabled={disabled || isDisabledSection(section.code)}
                      />
                    </div>
                  </td>
                  <td>
                    <SectionName
                      configurationId={configuration.id}
                      section={section}
                      disabled={disabled}
                      setSelectedSection={() => onSelectedSection(section)}
                    />
                  </td>
                  <td className="flex h-21 justify-center">
                    {section.include ? (
                      <div className="flex flex-col items-center justify-center">
                        {isNarrativeSection(section.code) ? (
                          <span
                            className="text-gray-cool-90 whitespace-nowrap italic"
                            aria-hidden
                          >
                            Not applicable for this section
                          </span>
                        ) : (
                          <RefineSwitch
                            configurationId={configuration.id}
                            currentSection={section}
                            sections={configuration.section_processing}
                            disabled={
                              disabled || isDisabledSection(section.code)
                            }
                          />
                        )}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    {section.include ? (
                      <NarrativeSelect
                        configurationId={configuration.id}
                        currentSection={section}
                        disabled={disabled || isDisabledSection(section.code)}
                        isNarrativeOnly={isNarrativeSection(section.code)}
                        isReconstructable={isReconstructableSection(
                          section.code
                        )}
                        codedDataAction={section.action}
                      />
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </SectionErrorProvider>
  );
}

interface SectionNameProps {
  configurationId: string;
  section: DbConfigurationSectionProcessing;
  disabled: boolean;
  setSelectedSection: () => void;
}

function SectionName({
  configurationId,
  section,
  disabled,
  setSelectedSection,
}: SectionNameProps) {
  const isCustom = section.section_type === 'custom';

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span
          title={section.name}
          className={classNames('truncate', {
            italic: !section.include,
            'font-bold': section.include,
          })}
        >
          {section.name}
        </span>
        {isCustom ? <CustomSectionBadge /> : null}
      </div>
      <div className="flex items-center gap-2">
        <span title={section.code} className="truncate text-sm">
          {section.code}
        </span>
        {isCustom && !disabled ? (
          <div className="flex items-center gap-1">
            <EditButton
              name={section.name}
              setSelectedSection={setSelectedSection}
            />
            <span className="text-sm" aria-hidden>
              |
            </span>
            <DeleteButton
              configurationId={configurationId}
              code={section.code}
              name={section.name}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}

interface EditButtonProps {
  setSelectedSection: () => void;
  name: string;
}

function EditButton({ setSelectedSection, name }: EditButtonProps) {
  return (
    <Button
      aria-label={`Edit custom section ${name}`}
      className="p-0! text-sm!"
      variant="tertiary"
      onClick={setSelectedSection}
    >
      Edit
    </Button>
  );
}

interface DeleteButtonProps {
  configurationId: string;
  code: string;
  name: string;
}

function DeleteButton({ configurationId, code, name }: DeleteButtonProps) {
  const { mutate } = useDeleteCustomSection();
  const queryClient = useQueryClient();
  const showToast = useToast();

  const onClick = () => {
    mutate(
      {
        configurationId,
        data: {
          code,
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          showToast({
            heading: 'Custom section deleted',
            body: name,
          });
        },
        onError: () => {
          {
            showToast({
              heading: 'Custom section could not be deleted',
              body: name,
              variant: 'error',
            });
          }
        },
      }
    );
  };

  return (
    <Button
      aria-label={`Delete custom section ${name}`}
      className="p-0! text-sm!"
      variant="tertiary"
      onClick={onClick}
    >
      Delete
    </Button>
  );
}

interface SelectionToggleProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  sections: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

function IncludeSwitch({
  currentSection,
  configurationId,
  disabled,
}: SelectionToggleProps) {
  const updateSection = useSectionUpdater(configurationId);
  const { clearError } = useSectionError();

  return (
    <Switch
      variant="violet"
      aria-label={`Include ${currentSection.name} section rules in refined document.`}
      checked={currentSection.include}
      disabled={disabled}
      onChange={(checked) => {
        clearError();
        updateSection(currentSection, { include: checked });
      }}
    />
  );
}

function RefineSwitch({
  currentSection,
  configurationId,
  disabled,
}: SelectionToggleProps) {
  const updateSection = useSectionUpdater(configurationId);
  const { clearError, setError, errorSectionCode } = useSectionError();

  const refineLabelText = CodedDataLabelsValue.refine;
  const retainLabelText = CodedDataLabelsValue.retain;
  const curSectionSetToRefine =
    currentSection.action === DbSectionAction.refine;

  const [toggled, setToggled] = useState(curSectionSetToRefine);

  const handleSwitchChange = async () => {
    // TODO: This validation should eventually be enforced by backend API as well
    if (
      currentSection.narrative === 'reconstruct' ||
      currentSection.narrative === 'keep_on_match'
    ) {
      setError(currentSection.code);

      // set toggled state back and forth on a sleep to give user some visual feedback
      // that their click registered
      setToggled(false);
      await new Promise((resolve) => setTimeout(resolve, 300));
      setToggled(true);
      return;
    }
    clearError();
    updateSection(currentSection, {
      action: toggled ? DbSectionAction.retain : DbSectionAction.refine,
    });
    setToggled((prev) => !prev);
  };

  const showError = errorSectionCode === currentSection.code;

  return (
    <div
      className="grid grid-cols-1 grid-rows-1 place-items-end"
      data-error-trigger
    >
      <div className="z-5 col-start-1 row-start-1">
        <Field className="flex flex-row items-center justify-end">
          <Label
            aria-label={
              curSectionSetToRefine
                ? // "Refine Admission Diagnosis section"
                  `${refineLabelText} ${currentSection.name} section`
                : // "Keep original for Admission Diagnosis section"
                  `${retainLabelText} for ${currentSection.name} section`
            }
          >
            {curSectionSetToRefine ? (
              <span>{refineLabelText}</span>
            ) : (
              <span className="italic">{retainLabelText}</span>
            )}
          </Label>
          <Switch
            variant="blue"
            disabled={disabled}
            checked={toggled}
            onChange={handleSwitchChange}
          />
        </Field>
      </div>
      {showError && (
        <p
          className="text-state-error-dark col-start-1 row-start-1 translate-y-5 text-xs whitespace-nowrap"
          role="alert"
        >
          {currentSection.narrative === 'reconstruct'
            ? 'To reconstruct narrative, refine must be selected'
            : 'To keep narrative on match, refine must be selected'}
        </p>
      )}
    </div>
  );
}

import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import {
  DbSectionAction,
  DisabledSection,
  NarrativeOnlySection,
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
import { Checkbox } from '@components/Checkbox';
import { Switch } from './Switch';
import { NarrativeSelect } from './NarrativeSelect';
import { useSectionUpdater } from './useSectionUpdater';
import { SectionErrorProvider } from './SectionErrorProvider';
import { useSectionError } from './useSectionError';
import classNames from 'classnames';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Tooltip } from '@components/Tooltip';

interface SectionsProps {
  configurationId: string;
  sections: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

export function Sections({
  configurationId,
  sections: sectionProcessing,
  disabled,
}: SectionsProps) {
  const [selectedSection, setSelectedSection] =
    useState<DbConfigurationSectionProcessing | null>(null);
  const [isOpen, setIsOpen] = useState(false);

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

  const onSelectedSection = (section: DbConfigurationSectionProcessing) => {
    setSelectedSection(section);
    setIsOpen(true);
  };

  const resetModal = () => {
    setSelectedSection(null);
  };

  return (
    <SectionErrorProvider>
      <section className="flex min-h-0 w-full flex-1 flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-cool-90 text-xl font-bold">
              eICR Sections
            </h3>
            {disabled ? null : (
              <Button
                variant="tertiary"
                onClick={() => {
                  setSelectedSection(null);
                  setIsOpen(true);
                }}
              >
                Add custom section <span aria-hidden>+</span>
              </Button>
            )}
            <CustomSectionModal
              isOpen={isOpen}
              setIsOpen={setIsOpen}
              configurationId={configurationId}
              initialSection={
                selectedSection
                  ? {
                      name: selectedSection.name,
                      currentCode: selectedSection.code,
                    }
                  : null
              }
              onClose={resetModal}
            />
          </div>
          <p className="italic">
            Choose which sections of your eICR to include, as well as whether to
            refine or retain each section.
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-scroll">
          <table className="w-full table-fixed">
            <thead className="sticky top-0 z-10 bg-white">
              <tr className="border-gray-cool-20 text-gray-cool-60 border-b">
                <th scope="col" className="w-20 py-3">
                  Include
                </th>
                <th scope="col" className="w-70 text-left">
                  Section name
                </th>
                <th scope="col" className="w-60 pr-8">
                  <div className="flex justify-end gap-1">
                    <span>Coded data</span>
                    <Tooltip
                      position="left"
                      label="Keep all original coded data included in the section, or set to Refine to choose the data you want to retain."
                    />
                  </div>
                </th>
                <th scope="col" className="w-40">
                  <div className="flex gap-1">
                    <span>Narrative data</span>
                    <Tooltip
                      position="left"
                      label="Keep the original data included in the narrative block, reconstruct the data from refined coded data, or omit exclude the narrative block for this section."
                    />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-gray-cool-20 divide-y">
              {sectionProcessing.map((section) => (
                <tr key={section.code} className="text-gray-cool-60">
                  <td>
                    <div className="flex justify-center p-8">
                      <IncludeCheckbox
                        configurationId={configurationId}
                        currentSection={section}
                        sections={sectionProcessing}
                        disabled={disabled || isDisabledSection(section.code)}
                      />
                    </div>
                  </td>
                  <td>
                    <SectionName
                      configurationId={configurationId}
                      section={section}
                      disabled={disabled}
                      setSelectedSection={() => onSelectedSection(section)}
                    />
                  </td>
                  <td className="pr-8">
                    {section.include ? (
                      <RefineSwitch
                        configurationId={configurationId}
                        currentSection={section}
                        sections={sectionProcessing}
                        disabled={disabled || isDisabledSection(section.code)}
                        isNarrativeOnly={isNarrativeSection(section.code)}
                      />
                    ) : null}
                  </td>
                  <td>
                    {section.include ? (
                      <NarrativeSelect
                        configurationId={configurationId}
                        currentSection={section}
                        disabled={disabled || isDisabledSection(section.code)}
                        isNarrativeOnly={isNarrativeSection(section.code)}
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

function IncludeCheckbox({
  currentSection,
  configurationId,
  disabled,
}: SelectionToggleProps) {
  const updateSection = useSectionUpdater(configurationId);
  const { clearError } = useSectionError();

  return (
    <Checkbox
      id={`${currentSection.name}-include`}
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
  isNarrativeOnly,
}: SelectionToggleProps & {
  isNarrativeOnly: boolean;
}) {
  const updateSection = useSectionUpdater(configurationId);
  const { clearError, setError, errorSectionCode } = useSectionError();

  if (isNarrativeOnly) {
    return (
      <Field className="flex flex-row items-center justify-end">
        <Label
          className="text-gray-cool-40 whitespace-nowrap italic"
          aria-hidden
        >
          Not applicable for this section
        </Label>
      </Field>
    );
  }

  const isRefineToggled = currentSection.action === DbSectionAction.refine;
  const refineLabelText = 'Refine';
  const preserveLabelText = 'Keep original';

  const handleSwitchChange = (checked: boolean) => {
    // TODO: This validation should eventually be enforced by backend API as well
    if (!checked && currentSection.narrative === 'reconstruct') {
      setError(currentSection.code);
      return;
    }
    clearError();
    updateSection(currentSection, {
      action: checked ? DbSectionAction.refine : DbSectionAction.retain,
    });
  };

  const showError = errorSectionCode === currentSection.code;

  return (
    <div className="flex flex-col items-end gap-1" data-error-trigger>
      <Field className="flex flex-row items-center justify-end">
        <Label
          aria-label={
            isRefineToggled
              ? // "Refine Admission Diagnosis section"
                `${refineLabelText} ${currentSection.name} section`
              : // "Keep original for Admission Diagnosis section"
                `${preserveLabelText} for ${currentSection.name} section`
          }
        >
          {isRefineToggled ? (
            <span>{refineLabelText}</span>
          ) : (
            <span className="italic">{preserveLabelText}</span>
          )}
        </Label>
        <Switch
          disabled={disabled}
          checked={isRefineToggled}
          onChange={handleSwitchChange}
        />
      </Field>
      {showError && (
        <p className="text-state-error-dark text-xs whitespace-nowrap" role="alert">
          To reconstruct narrative, refine must be selected
        </p>
      )}
    </div>
  );
}

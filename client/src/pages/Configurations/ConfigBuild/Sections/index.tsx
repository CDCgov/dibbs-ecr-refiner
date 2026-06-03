import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import {
  DbSectionAction,
  DisabledSection,
  NarrativeOnlySection,
} from '../../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useUpdateSection,
  useDeleteCustomSection,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Button } from '@components/Button';
import { CustomSectionModal } from './CustomSectionModal';
import { CustomSectionBadge } from './CustomSectionBadge';
import { Checkbox } from '@components/Checkbox';
import { Switch } from './Switch';
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
    <section className="flex min-h-0 w-full flex-1 flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-gray-cool-90 text-xl font-bold">eICR Sections</h3>
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
        {/* TODO: Revisit table layout for Refiner 2.0 UI migration. Evaluate
            whether a virtualized list is appropriate for large section counts.
            */}
        <table className="w-full table-fixed">
          <thead className="sticky top-0 z-10 bg-white">
            <tr className="border-gray-cool-20 text-gray-cool-60 border-b">
              <th scope="col" className="w-[10%] pt-3 pb-3">
                Include
              </th>
              <th scope="col" className="w-[40%] pt-3 pb-3 text-left">
                Section name
              </th>
              <th scope="col" className="align-right w-[33%] pt-3 pb-3">
                <div className="flex items-center justify-center gap-1">
                  <span>Coded data</span>
                  <Tooltip
                    position="left"
                    label="Keep all original coded data included in the section, or set to Refine to choose the data you want to retain."
                  />
                </div>
              </th>
              <th scope="col" className="w-[17%] pt-3 pb-3">
                <div className="flex items-center justify-center gap-1">
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
                <td className="w-[10%]">
                  <div className="flex justify-center p-8">
                    <IncludeCheckbox
                      configurationId={configurationId}
                      currentSection={section}
                      sections={sectionProcessing}
                      disabled={disabled || isDisabledSection(section.code)}
                    />
                  </div>
                </td>
                <td className="w-[40%]">
                  <SectionName
                    configurationId={configurationId}
                    section={section}
                    disabled={disabled}
                    setSelectedSection={() => onSelectedSection(section)}
                  />
                </td>
                <td className="w-[33%]">
                  {section.include ? (
                    <div className="flex justify-center">
                      {isNarrativeSection(section.code) ? (
                        <span
                          className="text-gray-cool-50 text-center italic lg:text-right"
                          aria-hidden
                        >
                          Not applicable for this section
                        </span>
                      ) : (
                        <RefineSwitch
                          configurationId={configurationId}
                          currentSection={section}
                          sections={sectionProcessing}
                          disabled={disabled || isDisabledSection(section.code)}
                        />
                      )}
                    </div>
                  ) : null}
                </td>
                <td className="w-[17%]">
                  {section.include ? (
                    <div className="flex justify-center">
                      <NarrativeSwitch
                        configurationId={configurationId}
                        currentSection={section}
                        sections={sectionProcessing}
                        disabled={disabled || isDisabledSection(section.code)}
                      />
                    </div>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
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
        <span className="truncate text-sm">{section.code}</span>
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
      className="text-sm!"
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
      className="text-sm!"
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

  return (
    <Checkbox
      id={`${currentSection.name}-include`}
      aria-label={`Include ${currentSection.name} section rules in refined document.`}
      checked={currentSection.include}
      disabled={disabled}
      onChange={(checked) => {
        updateSection(currentSection, { include: checked });
      }}
    />
  );
}

type SectionPatch = Partial<
  Pick<
    DbConfigurationSectionProcessing,
    'action' | 'include' | 'narrative' | 'code'
  >
>;

function useSectionUpdater(configurationId: string) {
  const { mutate: updateSection } = useUpdateSection();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  return (
    currentSection: DbConfigurationSectionProcessing,
    patch: SectionPatch
  ) => {
    updateSection(
      {
        configurationId,
        data: {
          action: patch.action ?? currentSection.action,
          current_code: patch.code ?? currentSection.code,
          include: patch.include ?? currentSection.include,
          narrative: patch.narrative ?? currentSection.narrative,
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            heading: 'Section failed to update',
            body: errorDetail,
            variant: 'error',
          });
        },
      }
    );
  };
}

function RefineSwitch({
  currentSection,
  configurationId,
  disabled,
}: SelectionToggleProps) {
  const updateSection = useSectionUpdater(configurationId);

  const isRefineToggled = currentSection.action === DbSectionAction.refine;
  const refineLabelText = 'Refine';
  const preserveLabelText = 'Keep original';

  return (
    <Field className="flex -translate-x-4 flex-row items-center">
      <Label
        aria-label={
          isRefineToggled
            ? // "Refine Admission Diagnosis section"
              `${refineLabelText} ${currentSection.name} section`
            : // "Keep original for Admission Diagnosis section"
              `${preserveLabelText} for ${currentSection.name} section`
        }
        className="mr-2 w-48 text-right"
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
        onChange={(checked) => {
          updateSection(currentSection, {
            action: checked ? DbSectionAction.refine : DbSectionAction.retain,
          });
        }}
      />
    </Field>
  );
}

function NarrativeSwitch({
  currentSection,
  configurationId,
  disabled,
}: SelectionToggleProps) {
  const updateSection = useSectionUpdater(configurationId);

  return (
    <Field className="flex items-center gap-3">
      <Switch
        disabled={disabled}
        checked={currentSection.narrative}
        onChange={(checked) => {
          updateSection(currentSection, {
            narrative: checked,
          });
        }}
        aria-label={`Toggle to refine or retain the narrative block in the ${currentSection.name} section`}
      />
    </Field>
  );
}

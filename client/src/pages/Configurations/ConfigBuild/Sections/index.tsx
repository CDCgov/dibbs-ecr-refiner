import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { Field, Label } from '@headlessui/react';
import { DbSectionAction } from '../../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useUpdateSection,
  useDeleteCustomSection,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Button } from '../../../../components/Button';
import { Modal } from './Modal';
import { CustomSectionBadge } from './CustomSectionBadge';
import { Tooltip } from './Tooltip';
import { Checkbox } from './Checkbox';
import { Switch } from './Switch';
import classNames from 'classnames';

/**
 * TODO: please refer to specification.py
 *
 * These sections are "skipped" so we don't allow users to make selections for them.
 * This will change in the future when we know how the sections will be used.
 * Ask @robertmitchellv about this for more detail.
 */

const disabledSections = new Set(['88085-6', '83910-0']);

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

  const onSelectedSection = (section: DbConfigurationSectionProcessing) => {
    setSelectedSection(section);
    setIsOpen(true);
  };

  const resetModal = () => {
    setSelectedSection(null);
  };

  return (
    <section className="flex w-full flex-col gap-6">
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
          <Modal
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

      <table className="w-full table-fixed">
        <thead>
          <tr className="border-gray-cool-20 text-gray-cool-60 border-b">
            <th scope="col" className="w-32 pb-3">
              Include
            </th>
            <th scope="col" className="w-auto pb-3 text-left">
              Section name
            </th>
            <th scope="col" className="align-right w-2/6 pb-3">
              <div className="flex items-center justify-center gap-1">
                <span>Data handling approach</span>
                <Tooltip
                  text={`Set to "Refine & optimize" if you'd like to filter the content of this section down to coded elements matching the codes in your configuration in your refined output. Set to "Preserve & retain" if you'd like to keep the information in this section in its entirety in the refined output.`}
                />
              </div>
            </th>
            <th scope="col" className="w-1/6 pb-3">
              <div className="flex items-center justify-center gap-1">
                <span>Narrative</span>
                <Tooltip text="Enable to retain the narrative block for this section in the refined output or disable to omit it." />
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
                    disabled={disabled || disabledSections.has(section.code)}
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
              <td>
                {section.include ? (
                  <div className="flex justify-center">
                    <RefineSwitch
                      configurationId={configurationId}
                      currentSection={section}
                      sections={sectionProcessing}
                      disabled={disabled || disabledSections.has(section.code)}
                    />
                  </div>
                ) : null}
              </td>

              <td>
                {section.include ? (
                  <div className="flex justify-center">
                    <NarrativeSwitch
                      configurationId={configurationId}
                      currentSection={section}
                      sections={sectionProcessing}
                      disabled={disabled || disabledSections.has(section.code)}
                    />
                  </div>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
      {isCustom ? (
        <div className="flex gap-2">
          <span className="truncate text-sm">{section.code}</span>
          {disabled ? null : (
            <div className="flex gap-1">
              <EditButton setSelectedSection={setSelectedSection} />
              <span className="text-sm" aria-hidden>
                |
              </span>
              <DeleteButton
                configurationId={configurationId}
                code={section.code}
                name={section.name}
              />
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

interface EditButtonProps {
  setSelectedSection: () => void;
}

function EditButton({ setSelectedSection }: EditButtonProps) {
  return (
    <Button
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
    <Button className="text-sm!" variant="tertiary" onClick={onClick}>
      Delete
    </Button>
  );
}

function IncludeCheckbox({
  currentSection,
  configurationId,
  disabled,
}: SwitchProps) {
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
    >
      <svg
        className="group-data-checked:bg-blue-cool-50 hidden stroke-white group-data-checked:block"
        viewBox="0 0 14 14"
        fill="none"
      >
        <path
          d="M3 8L6 11L11 3.5"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </Checkbox>
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

interface SwitchProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  sections: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

function RefineSwitch({
  currentSection,
  configurationId,
  disabled,
}: SwitchProps) {
  const updateSection = useSectionUpdater(configurationId);

  const isRefineToggled = currentSection.action === DbSectionAction.refine;
  const refineLabelText = 'Refine & optimize';
  const preserveLabelText = 'Preserve & retain all data';

  return (
    <Field className="flex -translate-x-4 items-center">
      <Label
        aria-label={
          isRefineToggled
            ? // "Refine & optimize Admission Diagnosis section"
              `${refineLabelText} ${currentSection.name} section`
            : // "Preserve & retain all data for Admission Diagnosis section"
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
}: SwitchProps) {
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

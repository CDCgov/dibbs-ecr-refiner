import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { Switch, Checkbox, Field, Label } from '@headlessui/react';
import { DbSectionAction } from '../../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useUpdateSection,
  useDeleteCustomSection,
  useAddCustomSection,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import {
  ModalRef,
  Tooltip as USWDSTooltip,
  Modal as USWDSModal,
  ModalFooter,
  ModalHeading,
  ButtonGroup,
  TextInput,
  Label as USWDSLabel,
} from '@trussworks/react-uswds';
import React, { JSX, useRef, useState } from 'react';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';
import { Button } from '../../../../components/Button';

/**
 * TODO: please refer to specification.py
 *
 * These sections are "skipped" so we don't allow users to make selections for them.
 * This will change in the future when we know how the sections will be used.
 * Ask @robertmitchellv about this for more detail.
 */

const disabledSections = new Set(['88085-6', '83910-0']);

type ModalState = 'add' | 'edit';

interface SectionsProps {
  configurationId: string;
  sections: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

/**
 * EicrSectionReview displays an overview or review of eICR sections and allows
 * users to choose an action for each section (retain, refine, remove).
 * Radio inputs are fully accessible and can be selected by clicking anywhere
 * in the containing table cell (td), supporting keyboard navigation as well.
 */
export function Sections({
  configurationId,
  sections: sectionProcessing,
  disabled,
}: SectionsProps) {
  const modalRef = useRef<ModalRef>(null);
  const [mode, setMode] = useState<ModalState>('add');
  const [selectedSection, setSelectedSection] =
    useState<DbConfigurationSectionProcessing | null>(null);

  const resetModal = () => {
    setMode('add');
    setSelectedSection(null);
  };

  return (
    <section className="flex w-full flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-gray-cool-90 text-xl font-bold">eICR Sections</h3>
          {disabled ? null : (
            <ModalToggleButton modalRef={modalRef} variant="tertiary" opener>
              Add custom section +
            </ModalToggleButton>
          )}
          <Modal
            configurationId={configurationId}
            ref={modalRef}
            mode={mode}
            initialSection={
              selectedSection
                ? {
                    name: selectedSection?.name,
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

      <table className="w-full">
        <thead>
          <tr className="border-gray-cool-20 text-gray-cool-60 border-b">
            <th scope="col" className="w-1/6 pb-3">
              Include
            </th>
            <th scope="col" className="w-2/6 pb-3 text-left">
              Section name
            </th>
            <th scope="col" className="w-3/6 pb-3">
              <div className="flex items-center justify-center gap-1">
                <span>Data handling approach</span>
                <Tooltip
                  text={`Set to "Refine & optimize" if you'd like to filter the content of this section down to coded elements matching the codes in your configuration in your refined output. Set to "Preserve & retain" if you'd like to keep the information in this section in its entirety in the refined output.`}
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
                    disabled={disabled || disabledSections.has(section.code)}
                  />
                </div>
              </td>
              <td>
                <SectionName
                  configurationId={configurationId}
                  section={section}
                  modalRef={modalRef}
                  setEditMode={() => setMode('edit')}
                  setSelectedSection={() => setSelectedSection(section)}
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
  modalRef: React.RefObject<ModalRef | null>;
  setEditMode: () => void;
  setSelectedSection: () => void;
}

function SectionName({
  configurationId,
  section,
  modalRef,
  setEditMode,
  setSelectedSection,
}: SectionNameProps) {
  const isCustom = section.section_type === 'custom';

  if (section.include) {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-bold">{section.name}</span>
          {isCustom ? <CustomSectionBadge /> : null}
        </div>
        {isCustom ? (
          <div className="flex flex-row gap-2">
            <span className="text-sm">{section.code}</span>
            <div className="flex flex-row gap-1">
              <EditButton
                modalRef={modalRef}
                setEditMode={setEditMode}
                setSelectedSection={setSelectedSection}
              />
              <span className="not-sr-only text-sm">|</span>
              <DeleteButton
                configurationId={configurationId}
                code={section.code}
              />
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span className="text-gray-cool-70 italic">{section.name}</span>
        {isCustom ? <CustomSectionBadge /> : null}
      </div>
      {isCustom ? <span className="text-sm">{section.code}</span> : null}
    </div>
  );
}

function CustomSectionBadge() {
  return (
    <span className="bg-gray-cool-3 flex items-center justify-center rounded-sm px-2 py-0.5 text-sm">
      Custom
    </span>
  );
}

interface EditButtonProps {
  setEditMode: () => void;
  setSelectedSection: () => void;
  modalRef: React.RefObject<ModalRef | null>;
}

function EditButton({
  setEditMode,
  setSelectedSection,
  modalRef,
}: EditButtonProps) {
  return (
    <ModalToggleButton
      className="text-sm!"
      variant="tertiary"
      modalRef={modalRef}
      onClick={() => {
        setEditMode();
        setSelectedSection();
      }}
    >
      Edit
    </ModalToggleButton>
  );
}

interface DeleteButtonProps {
  configurationId: string;
  code: string;
}

function DeleteButton({ configurationId, code }: DeleteButtonProps) {
  const { mutate } = useDeleteCustomSection();
  const queryClient = useQueryClient();

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

interface EditCustomSection {
  name: string;
  currentCode: string;
}

interface ModalProps {
  ref: React.RefObject<ModalRef | null>;
  configurationId: string;
  mode: 'add' | 'edit';
  onClose?: () => void;
  initialSection?: EditCustomSection | null;
}

function Modal({
  ref,
  configurationId,
  mode,
  onClose,
  initialSection,
}: ModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initialSection?.name ?? '');
  const [newCode, setNewCode] = useState(initialSection?.currentCode ?? '');
  const [errorText, setErrorText] = useState('');
  const { mutate: addCustomSection } = useAddCustomSection();
  const { mutate: updateCustomSection } = useUpdateSection();

  if (initialSection && !name && !newCode) {
    setName(initialSection.name);
    setNewCode(initialSection.currentCode);
  }

  const isEdit = mode === 'edit';

  const clearForm = () => {
    setName('');
    setNewCode('');
    setErrorText('');
    onClose?.();
  };

  const onSubmit = () => {
    const trimmedName = name.trim();
    const trimmedCode = newCode.trim();

    if (!trimmedName) {
      setErrorText('Name is required.');
      return;
    }

    if (!trimmedCode) {
      setErrorText('Code is required.');
      return;
    }

    if (isEdit && initialSection) {
      updateCustomSection(
        {
          configurationId,
          data: {
            name: trimmedName,
            new_code: trimmedCode,
            current_code: initialSection.currentCode,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            clearForm();
          },
          onError: () => {
            setErrorText('Unable to update custom section.');
          },
        }
      );
      return;
    }

    addCustomSection(
      {
        configurationId,
        data: {
          code: newCode,
          name,
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          clearForm();
        },
        onError: () => {
          setErrorText('Unable to add custom section.');
        },
      }
    );
  };

  return (
    <USWDSModal
      className="rounded-sm"
      ref={ref}
      id="custom-section-modal"
      aria-labelledby="modal-heading"
      aria-describedby="modal-description"
    >
      <div className="flex flex-col items-start gap-6 p-5">
        <ModalHeading
          className="font-public-sans! text-2xl!"
          id="modal-heading"
        >
          {isEdit ? 'Edit custom section' : 'Add a custom section'}
        </ModalHeading>
        <div className="flex flex-col items-start">
          <p id="modal-description" className="sr-only">
            Enter your custom section information and click "Add section".
          </p>
          <div className="flex flex-col gap-3">
            <div>
              <USWDSLabel htmlFor="custom-section-name-input">
                Display name (for this section)
              </USWDSLabel>
              <TextInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                id="custom-section-name-input"
                name="custom-section-name-input"
                type="text"
              />
            </div>
            <div>
              <USWDSLabel htmlFor="custom-section-code-input">
                LOINC code
              </USWDSLabel>
              <TextInput
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                id="custom-section-code-input"
                name="custom-section-code-input"
                type="text"
              />
            </div>
            {errorText ? (
              <p className="text-secondary-dark text-sm">{errorText}</p>
            ) : null}
          </div>
        </div>
        <ModalFooter>
          <ButtonGroup>
            <ModalToggleButton modalRef={ref} onClick={onSubmit} closer>
              {isEdit ? 'Update section' : 'Add section'}
            </ModalToggleButton>
            <ModalToggleButton variant="tertiary" modalRef={ref} closer>
              Cancel
            </ModalToggleButton>
          </ButtonGroup>
        </ModalFooter>
      </div>
    </USWDSModal>
  );
}

interface RefineSwitchProps {
  configurationId: string;
  currentSection: DbConfigurationSectionProcessing;
  sections: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

function IncludeCheckbox({
  currentSection,
  configurationId,
  disabled,
}: RefineSwitchProps) {
  const { mutate: updateSection } = useUpdateSection();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  return (
    <Checkbox
      className="group block size-5 cursor-pointer rounded border bg-white data-checked:bg-blue-500 data-disabled:cursor-not-allowed data-disabled:opacity-50 data-checked:data-disabled:bg-gray-500"
      id={`${currentSection.name}-include`}
      aria-label={`Include ${currentSection.name} section rules in refined document.`}
      checked={currentSection.include}
      disabled={disabled}
      onChange={(checked) => {
        const include = checked;
        const updatedSection: DbConfigurationSectionProcessing = {
          ...currentSection,
          include,
        };

        updateSection(
          {
            configurationId,
            data: {
              action: updatedSection.action,
              current_code: updatedSection.code,
              include: updatedSection.include,
              narrative: false, // TODO: Update later
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

function RefineSwitch({
  currentSection,
  configurationId,
  disabled,
}: RefineSwitchProps) {
  const { mutate: updateSection } = useUpdateSection();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  const isRefineToggled = currentSection.action === DbSectionAction.refine;
  const refineLabelText = 'Refine & optimize';
  const preserveLabelText = 'Preserve & retain all data';

  return (
    <Field className="flex items-center">
      <Label
        aria-label={
          isRefineToggled
            ? // "Refine & optimize Admission Diagnosis section"
              `${refineLabelText} ${currentSection.name} section`
            : // "Preserve & retain all data for Admission Diagnosis section"
              `${preserveLabelText} for ${currentSection.name} section`
        }
        className="w-48"
      >
        {isRefineToggled ? (
          <span>{refineLabelText}</span>
        ) : (
          <span className="italic">{preserveLabelText}</span>
        )}
      </Label>
      <Switch
        className="group data-checked:bg-violet-warm-60 bg-gray-cool-60 inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition data-disabled:cursor-not-allowed data-disabled:opacity-50"
        disabled={disabled}
        checked={isRefineToggled}
        onChange={(checked) => {
          const action: DbSectionAction = checked
            ? DbSectionAction.refine
            : DbSectionAction.retain;
          const updatedSection: DbConfigurationSectionProcessing = {
            ...currentSection,
            action,
          };

          updateSection(
            {
              configurationId,
              data: {
                action: updatedSection.action,
                current_code: updatedSection.code,
                include: updatedSection.include,
                narrative: false, // TODO: Update later
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
        }}
      >
        <span className="data-disabled:bg-gray-cool-60 pointer-events-none size-4 translate-x-1 rounded-full bg-white transition group-data-checked:translate-x-6" />
      </Switch>
    </Field>
  );
}

function InfoIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9.16675 5.83366H10.8334V7.50033H9.16675V5.83366ZM9.16675 9.16699H10.8334V14.167H9.16675V9.16699ZM10.0001 1.66699C5.40008 1.66699 1.66675 5.40033 1.66675 10.0003C1.66675 14.6003 5.40008 18.3337 10.0001 18.3337C14.6001 18.3337 18.3334 14.6003 18.3334 10.0003C18.3334 5.40033 14.6001 1.66699 10.0001 1.66699ZM10.0001 16.667C6.32508 16.667 3.33341 13.6753 3.33341 10.0003C3.33341 6.32533 6.32508 3.33366 10.0001 3.33366C13.6751 3.33366 16.6667 6.32533 16.6667 10.0003C16.6667 13.6753 13.6751 16.667 10.0001 16.667Z"
        fill="#3A7D95"
      />
    </svg>
  );
}

type CustomTooltipProps = JSX.IntrinsicElements['div'] &
  React.RefAttributes<HTMLDivElement>;

const CustomLinkForwardRef: React.ForwardRefRenderFunction<
  HTMLDivElement,
  CustomTooltipProps
> = ({ ...tooltipProps }: CustomTooltipProps, ref) => (
  <div {...tooltipProps} ref={ref}>
    <InfoIcon />
  </div>
);

const CustomTooltip = React.forwardRef(CustomLinkForwardRef);

interface TooltipProps {
  text: string;
}
function Tooltip({ text }: TooltipProps) {
  return (
    <USWDSTooltip<CustomTooltipProps>
      position="left"
      label={<div className="w-max max-w-75 whitespace-normal">{text}</div>}
      asCustom={CustomTooltip}
    >
      Data handling approach tooltip
    </USWDSTooltip>
  );
}

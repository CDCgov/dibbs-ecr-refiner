import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { Switch, Checkbox, Field, Label } from '@headlessui/react';
import { DbSectionAction } from '../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useUpdateConfigurationSectionProcessing,
} from '../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { Tooltip as USWDSTooltip } from '@trussworks/react-uswds';
import React, { JSX } from 'react';
import { Button } from '../../../components/Button';

/**
 * TODO: please refer to specification.py
 *
 * These sections are "skipped" so we don't allow users to make selections for them.
 * This will change in the future when we know how the sections will be used.
 * Ask @robertmitchellv about this for more detail.
 */

const disabledSections = new Set(['88085-6', '83910-0']);

interface EicrSectionReviewProps {
  configurationId: string;
  sectionProcessing: DbConfigurationSectionProcessing[];
  disabled: boolean;
}

/**
 * EicrSectionReview displays an overview or review of eICR sections and allows
 * users to choose an action for each section (retain, refine, remove).
 * Radio inputs are fully accessible and can be selected by clicking anywhere
 * in the containing table cell (td), supporting keyboard navigation as well.
 */
export function EicrSectionReview({
  configurationId,
  sectionProcessing,
  disabled,
}: EicrSectionReviewProps) {
  return (
    <section className="flex w-full flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-gray-cool-90 text-xl font-bold">eICR Sections</h3>
          <Button variant="tertiary">Add custom section +</Button>
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
                {section.include ? (
                  <span className="font-bold">{section.name}</span>
                ) : (
                  <span className="text-gray-cool-70 italic">
                    {section.name}
                  </span>
                )}
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
  const { mutate: updateSectionProcessing } =
    useUpdateConfigurationSectionProcessing();
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

        updateSectionProcessing(
          {
            configurationId,
            data: {
              action: updatedSection.action,
              code: updatedSection.code,
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
  const { mutate: updateSectionProcessing } =
    useUpdateConfigurationSectionProcessing();
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
        passive
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

          updateSectionProcessing(
            {
              configurationId,
              data: {
                action: updatedSection.action,
                code: updatedSection.code,
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

import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';
import { useToast } from '../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { Switch, Checkbox } from '@headlessui/react';
import { DbSectionAction } from '../../../api/schemas';
import {
  getGetConfigurationQueryKey,
  useUpdateConfigurationSectionProcessing,
} from '../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';

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
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h3 className="text-gray-cool-90 text-xl font-bold">eICR Sections</h3>
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
            <th scope="col" className="w-3/6 pb-3 text-left">
              Section name
            </th>
            <th scope="col" className="w-1/3 pb-3">
              Data handling approach
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
                    disabled={disabled}
                  />
                </div>
              </td>
              <td className="px-3 py-3">
                {section.include ? (
                  <span className="font-bold">
                    {castToSentenceCase(section.name)}
                  </span>
                ) : (
                  <span className="text-gray-cool-70 italic">
                    {castToSentenceCase(section.name)}
                  </span>
                )}
              </td>
              <td className="px-3 py-2">
                {section.include ? (
                  <div className="flex justify-center">
                    <RefineSwitch
                      configurationId={configurationId}
                      currentSection={section}
                      sections={sectionProcessing}
                      disabled={disabled}
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
      className="group block size-5 rounded border bg-white data-checked:bg-blue-500 data-disabled:cursor-not-allowed data-disabled:opacity-50 data-checked:data-disabled:bg-gray-500"
      id={`${currentSection.name}-include`}
      checked={currentSection.include}
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
              section: {
                action: updatedSection.action,
                code: updatedSection.code,
                include: updatedSection.include,
              },
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
      disabled={disabled}
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

  return (
    <Switch
      disabled={disabled}
      checked={currentSection.action === DbSectionAction.refine}
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
              section: {
                action: updatedSection.action,
                code: updatedSection.code,
                include: updatedSection.include,
              },
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
      className="group data-checked:bg-violet-warm-60 inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition data-disabled:cursor-not-allowed data-disabled:opacity-50"
    >
      <span className="data-disabled:bg-gray-cool-60 size-4 translate-x-1 rounded-full bg-white transition group-data-checked:translate-x-6" />
    </Switch>
  );
}

function castToSentenceCase(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1, str.length).toLowerCase();
}

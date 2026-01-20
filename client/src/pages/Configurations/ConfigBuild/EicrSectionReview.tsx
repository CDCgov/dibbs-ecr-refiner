import { useState } from 'react';
import { Table } from '../../../components/Table';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';
import {
  getGetConfigurationQueryKey,
  useUpdateConfigurationSectionProcessing,
} from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';
import { UpdateSectionProcessingEntryAction } from '../../../api/schemas';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { RadioCell } from '../../../components/Button/RadioCell';
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
  // Store selected action for each section in state
  const [selectedActions, setSelectedActions] = useState<string[]>(
    sectionProcessing.map((section) => section.action ?? 'retain')
  );

  const showToast = useToast();
  const formatError = useApiErrorFormatter();

  const { mutate: updateSectionProcessing } =
    useUpdateConfigurationSectionProcessing();
  const queryClient = useQueryClient();

  /**
   * Central helper that updates local state and calls the backend API for a
   * single section action change.
   */
  const applyAction = (
    index: number,
    action: UpdateSectionProcessingEntryAction
  ) => {
    if (disabled) {
      return;
    }
    // Capture previous action so we can revert if the mutation fails
    const previousAction = selectedActions[index] ?? 'retain';

    // Optimistically update UI for immediate feedback
    setSelectedActions((prev) => {
      const next = [...prev];
      next[index] = action;
      return next;
    });

    updateSectionProcessing(
      {
        configurationId: configurationId,
        data: {
          sections: [
            {
              code: sectionProcessing[index].code,
              action: action,
            },
          ],
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
        },
        onError: (error) => {
          // Revert the optimistic UI change only if the UI still shows the
          // attempted (failed) action. This prevents clobbering newer user
          // changes that may have occurred while the request was in-flight.
          setSelectedActions((prev) => {
            if (prev[index] !== action) {
              return prev;
            }
            const next = [...prev];
            next[index] = previousAction;
            return next;
          });
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

  return (
    <section
      id="sections-table"
      aria-label="Choose what you'd like to do with the sections in your eICR"
    >
      <h1 className="mb-4! text-lg leading-10 font-bold">
        Choose what you'd like to do with the sections in your eICR
      </h1>
      <p className="mb-4!">
        Choose whether to refine, include fully, or omit sections of your eICR
        to save space and protect patient privacy.
      </p>
      <p className="mb-2! leading-8">Options:</p>
      <ul className="mb-4! list-inside list-disc pl-4">
        <li>
          <span className="font-bold">Include & refine section:</span> Includes
          only the coded data you've chosen to retain in your configuration.
        </li>
        <li>
          <span className="font-bold">Include entire section:</span> Includes
          everything from this section, ignoring your configuration.
        </li>
        <li>
          <span className="font-bold">Remove section:</span> Excludes this
          section from the eICR entirely.
        </li>
      </ul>
      <Table className="mt-2 max-w-185! border-separate! border-spacing-0 rounded-full border-l-0">
        <colgroup>
          <col className="w-65" />
          <col className="w-40" />
          <col className="w-40" />
          <col className="w-40" />
        </colgroup>
        <caption className="usa-sr-only">
          Choose actions for each eICR section
        </caption>
        <thead>
          <tr>
            <th scope="col" className="text-gray-cool-60!">
              Section name
            </th>
            <th scope="col" className="text-gray-cool-60! text-center">
              Include &amp; <br /> refine section
            </th>
            <th scope="col" className="text-gray-cool-60!text-center">
              Include <br /> entire section
            </th>
            <th scope="col" className="text-gray-cool-60! text-center">
              Remove section
            </th>
          </tr>
        </thead>
        <tbody>
          {sectionProcessing.map((section, index) => (
            <tr key={section.name}>
              <td className="cursor-default! font-bold! wrap-break-word! whitespace-normal!">
                {section.name}
              </td>
              <RadioCell
                index={index}
                action="refine"
                checked={selectedActions[index] === 'refine'}
                ariaLabel={`Include and refine section ${section.name}`}
                applyAction={applyAction}
                disabled={disabled}
              />
              <RadioCell
                index={index}
                action="retain"
                checked={selectedActions[index] === 'retain'}
                ariaLabel={`Include entire section ${section.name}`}
                applyAction={applyAction}
                disabled={disabled}
              />

              <RadioCell
                index={index}
                action="remove"
                checked={selectedActions[index] === 'remove'}
                ariaLabel={`Remove section ${section.name}`}
                applyAction={applyAction}
                disabled={disabled}
              />
            </tr>
          ))}
        </tbody>
      </Table>
    </section>
  );
}

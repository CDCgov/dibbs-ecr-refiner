import React, { useState, useEffect, KeyboardEvent } from 'react';
import Table from '../../../components/Table';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';
import { useUpdateConfigurationSectionProcessing } from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';
import { UpdateSectionProcessingEntryAction } from '../../../api/schemas';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';

/**
 * EicrSectionReview displays an overview or review of eICR sections and allows
 * users to choose an action for each section (retain, refine, remove).
 * Radio inputs are fully accessible and can be selected by clicking anywhere
 * in the containing table cell (td), supporting keyboard navigation as well.
 */
const EicrSectionReview: React.FC<{
  configurationId: string;
  sectionProcessing: DbConfigurationSectionProcessing[];
}> = ({ configurationId, sectionProcessing }) => {
  // Store selected action for each section in state
  const [selectedActions, setSelectedActions] = useState<string[]>([]);

  const showToast = useToast();
  const formatError = useApiErrorFormatter();

  const { mutate: updateSectionProcessing } =
    useUpdateConfigurationSectionProcessing();

  // Initialize state based on the sectionProcessing prop. Only initialize
  // when local state is empty or the number of sections changes so we don't
  // clobber optimistic UI updates while a mutation is in-flight.
  useEffect(() => {
    setSelectedActions((prev) => {
      if (prev.length === 0 || prev.length !== sectionProcessing.length) {
        return sectionProcessing.map((section) => section.action ?? 'retain');
      }
      return prev;
    });
  }, [sectionProcessing]);

  /**
   * Central helper that updates local state and calls the backend API for a
   * single section action change.
   */
  const applyAction = (
    index: number,
    action: UpdateSectionProcessingEntryAction
  ) => {
    // Capture previous action so we can revert if the mutation fails
    const previousAction = selectedActions[index] ?? 'retain';

    // Optimistically update UI for immediate feedback
    setSelectedActions((prev) => {
      const next = [...prev];
      next[index] = action;
      return next;
    });

    // Send patch to backend
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
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            heading: 'Section failed to update',
            body: errorDetail,
            variant: 'error',
          });

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
        },
      }
    );
  };

  /**
   * Handles keyboard navigation for selecting radios from the containing <td>.
   * Supports Space and Enter activation for accessibility.
   */
  const handleTdKeyDown = (
    event: KeyboardEvent<HTMLTableCellElement>,
    index: number,
    action: UpdateSectionProcessingEntryAction
  ) => {
    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      applyAction(index, action);
    }
  };

  /**
   * Renders a clickable, accessible table cell containing a radio input for a section action.
   * Uses USWDS radio markup/classes for consistent styling and accessibility.
   */
  /**
   * Simplified vanilla radio cell for bug isolation.
   */
  const RadioCell: React.FC<{
    index: number;
    action: UpdateSectionProcessingEntryAction;
    checked: boolean;
    ariaLabel: string;
  }> = ({ index, action, checked, ariaLabel }) => {
    // Restore accessibility and event handler conventions from original version
    return (
      <td
        className="cursor-pointer text-center"
        onClick={(e) => {
          // Prevent double-firing if radio itself is clicked
          if (!(e.target as HTMLElement).closest('input')) {
            applyAction(index, action);
          }
        }}
        tabIndex={0}
        role="radio"
        aria-checked={checked}
        onKeyDown={(e) => handleTdKeyDown(e, index, action)}
      >
        <label className="usa-radio m-0 flex items-center justify-center bg-transparent">
          <input
            className="usa-radio__input"
            type="radio"
            name={`section-${index}`}
            value={action}
            aria-label={ariaLabel}
            checked={checked}
            tabIndex={-1}
            onChange={() => applyAction(index, action)}
          />
          <span className="usa-radio__label -top-4.5 right-8"></span>
          <span className="usa-sr-only">{ariaLabel}</span>
        </label>
      </td>
    );
  };

  return (
    <section
      aria-label="Choose what you'd like to do with the sections in your eICR"
      className="prose w-full"
    >
      <h2 className="!mb-4 text-lg leading-10 font-bold">
        Choose what you'd like to do with the sections in your eICR
      </h2>
      <p className="!mb-4">
        Choose whether to refine, include fully, or omit sections of your eICR
        to save space and protect patient privacy.
      </p>
      <p className="!mb-2 leading-8">Options:</p>
      <ul className="!mb-4 list-inside list-disc pl-4">
        <li>
          <b>Include & refine section:</b> Includes only the coded data you've
          chosen to retain in your configuration.
        </li>
        <li>
          <b>Include entire section:</b> Includes everything from this section,
          ignoring your configuration.
        </li>
        <li>
          <b>Remove section:</b> Excludes this section from the eICR entirely.
        </li>
      </ul>
      <Table bordered className="margin-top-2 w-[800px] table-fixed" scrollable>
        <colgroup>
          <col className="w-[260px]" />
          <col className="w-[160px]" />
          <col className="w-[160px]" />
          <col className="w-[160px]" />
        </colgroup>
        <caption className="usa-sr-only">
          Choose actions for each eICR section
        </caption>
        <thead>
          <tr>
            <th scope="col">Section name</th>
            <th scope="col">Include &amp; refine section</th>
            <th scope="col">Include entire section</th>
            <th scope="col">Remove section</th>
          </tr>
        </thead>
        <tbody>
          {sectionProcessing.map((section, index) => (
            <tr key={section.name}>
              <td className="!font-bold">{section.name}</td>
              <RadioCell
                index={index}
                action="retain"
                checked={selectedActions[index] === 'retain'}
                ariaLabel={`Include and refine section ${section.name}`}
              />
              <RadioCell
                index={index}
                action="refine"
                checked={selectedActions[index] === 'refine'}
                ariaLabel={`Include entire section ${section.name}`}
              />
              <RadioCell
                index={index}
                action="remove"
                checked={selectedActions[index] === 'remove'}
                ariaLabel={`Remove section ${section.name}`}
              />
            </tr>
          ))}
        </tbody>
      </Table>
    </section>
  );
};

export default EicrSectionReview;

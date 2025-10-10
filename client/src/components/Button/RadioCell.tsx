import { UpdateSectionProcessingEntryAction } from '../../api/schemas';

export interface RadioCellProps {
  index: number;
  action: UpdateSectionProcessingEntryAction;
  checked: boolean;
  ariaLabel: string;
  applyAction: (
    index: number,
    action: UpdateSectionProcessingEntryAction
  ) => void;
}

/**
 * RadioCell renders a clickable, accessible table cell containing a radio input for a section action.
 * Uses USWDS radio markup/classes for consistent styling and accessibility.
 */
export function RadioCell({
  index,
  action,
  checked,
  ariaLabel,
  applyAction,
}: RadioCellProps) {
  return (
    <td
      className="text-center !break-all !whitespace-normal focus:outline-none"
      tabIndex={0}
      onClick={() => applyAction(index, action)}
      onKeyDown={(e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          applyAction(index, action);
        }
      }}
    >
      <label className="usa-radio m-0 block cursor-pointer bg-transparent">
        <input
          className="usa-radio__input"
          type="radio"
          name={`section-${index}`}
          value={action}
          aria-label={ariaLabel}
          checked={checked}
          tabIndex={-1}
          readOnly
        />
        <span className="usa-radio__label -top-4.5 right-0"></span>
        <span className="usa-sr-only">{ariaLabel}</span>
      </label>
    </td>
  );
}

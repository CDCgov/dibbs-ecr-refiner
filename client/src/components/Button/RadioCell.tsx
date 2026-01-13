import { UpdateSectionProcessingEntryAction } from '../../api/schemas';

import classNames from 'classnames';

export interface RadioCellProps {
  index: number;
  action: UpdateSectionProcessingEntryAction;
  checked: boolean;
  ariaLabel: string;
  disabled?: boolean;
  applyAction: (
    index: number,
    action: UpdateSectionProcessingEntryAction
  ) => void;
}

/**
 * Interaction is handled *only* through the radio input's onChange handler
 * to prevent double-firing and duplicate API calls.
 */
export function RadioCell({
  index,
  action,
  checked,
  ariaLabel,
  applyAction,
  disabled = false,
}: RadioCellProps) {
  return (
    <td
      className={classNames(
        'text-center',
        'break-all!',
        'whitespace-normal!',
        'focus:outline-none',
        { 'cursor-not-allowed': disabled }
      )}
      tabIndex={0}
      onClick={() => {
        applyAction(index, action);
      }}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          {
            applyAction(index, action);
          }
        }
      }}
    >
      <label
        className={classNames(
          'usa-radio',
          'm-0',
          'block',
          'bg-transparent',
          { 'cursor-pointer': !disabled },
          { 'cursor-not-allowed': disabled }
        )}
      >
        <input
          className="usa-radio__input"
          type="radio"
          name={`section-${index}`}
          value={action}
          aria-label={ariaLabel}
          checked={checked}
          tabIndex={-1}
          readOnly
          disabled={disabled}
          onChange={() => applyAction(index, action)}
        />
        <span className="usa-radio__label -top-4.5 right-0"></span>
        <span className="usa-sr-only">{ariaLabel}</span>
      </label>
    </td>
  );
}

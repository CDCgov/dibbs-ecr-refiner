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
 * Interaction is handled *only* through the radio input's onChange handler
 * to prevent double-firing and duplicate API calls.
 */
export function RadioCell({
  index,
  action,
  checked,
  ariaLabel,
  applyAction,
}: RadioCellProps) {
  return (
    <td className="text-center align-middle !break-all !whitespace-normal">
      <label className="usa-radio m-0 block cursor-pointer bg-transparent">
        <input
          className="usa-radio__input"
          type="radio"
          name={`section-${index}`}
          value={action}
          aria-label={ariaLabel}
          checked={checked}
          onChange={() => applyAction(index, action)}
        />
        <span className="usa-radio__label -top-4.5 right-0"></span>
        <span className="usa-sr-only">{ariaLabel}</span>
      </label>
    </td>
  );
}

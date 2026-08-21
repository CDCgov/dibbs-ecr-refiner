import { Combobox, ComboboxOptions } from '@headlessui/react';
import { ComponentProps } from 'react';
import cn from 'classnames';

/**
 * BaseCombobox provides a wrapper around HeadlessUI Combobox components
 * with a default z-index to prevent overlay issues.
 *
 * Use the `className` prop to override the z-index if the combobox
 * is used within a modal (e.g., use `z-[var(--z-modal-dropdown)]`).
 */
export const BaseCombobox = Combobox;

export function BaseComboboxOptions({
  className,
  ...props
}: ComponentProps<typeof ComboboxOptions>) {
  return (
    <ComboboxOptions
      className={cn('z-[var(--z-dropdown)]', className)}
      {...props}
    />
  );
}

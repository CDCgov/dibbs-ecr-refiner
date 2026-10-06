import { Combobox, ComboboxOptions } from '@headlessui/react';
import { ComponentProps } from 'react';
import classNames from 'classnames';

/**
 * BaseCombobox provides a wrapper around HeadlessUI Combobox components
 * with a default z-index to prevent overlay issues.
 *
 * Use the `className` prop to override the z-index if the combobox
 * is used within a modal (e.g., use `z-modal-dropdown`).
 */
export const BaseCombobox = Combobox;

export function BaseComboboxOptions({
  className,
  ...props
}: ComponentProps<typeof ComboboxOptions>) {
  return (
    <ComboboxOptions
      className={classNames('z-dropdown', className)}
      {...props}
    />
  );
}

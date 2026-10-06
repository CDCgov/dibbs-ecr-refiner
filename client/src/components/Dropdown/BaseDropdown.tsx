import { Menu, MenuButton, MenuItems } from '@headlessui/react';
import { ComponentProps } from 'react';
import classNames from 'classnames';

/**
 * BaseDropdown provides a wrapper around HeadlessUI Menu components
 * with a default z-index to prevent overlay issues.
 *
 * Use the `className` prop to override the z-index if the dropdown
 * is used within a modal (e.g., use `z-modal-dropdown`).
 */
export const BaseMenu = Menu;
export const BaseMenuButton = MenuButton;

export function BaseMenuItems({
  className,
  ...props
}: ComponentProps<typeof MenuItems>) {
  return (
    <MenuItems className={classNames('z-dropdown', className)} {...props} />
  );
}

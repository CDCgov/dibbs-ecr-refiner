import { Link } from 'react-router';
import classNames from 'classnames';
import {
  Button as HeadlessButton,
  ButtonProps as HeadlessButtonProps,
} from '@headlessui/react';

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary';

interface ButtonProps extends HeadlessButtonProps {
  children: React.ReactNode;
  variant?: ButtonVariant;
  to?: string;
  href?: string;
}

const sharedStyles =
  'm-0 appearance-none cursor-pointer text-center rounded justify-center items-center gap-2 mr-2 px-5 py-3 font-bold leading-none no-underline inline-flex';

const variantStyles: Record<ButtonVariant, string> = {
  primary: classNames(
    sharedStyles,
    'bg-violet-warm-60 hover:bg-violet-warm-70 text-white border-0'
  ),
  secondary: classNames(
    sharedStyles,
    'bg-white text-violet-warm-60 hover:text-violet-warm-70 hover:border-violet-warm-70 border-violet-warm-60 border-[2px]'
  ),
  tertiary: sharedStyles,
};

/**
 * Button component supporting multiple variants and behaviors,
 * including primary, secondary, and disabled styles, with optional
 * routing functionality.
 */
export function Button({
  children,
  variant = 'primary',
  type = 'button',
  href,
  to,
  onClick,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variantClass = classNames(variantStyles[variant], className);

  if (href) {
    return (
      <a href={href} className={variantClass}>
        {children}
      </a>
    );
  }

  if (to) {
    return (
      <Link
        to={to}
        onClick={
          onClick as unknown as React.MouseEventHandler<HTMLAnchorElement>
        }
        className={variantClass}
      >
        {children}
      </Link>
    );
  }

  return (
    <HeadlessButton
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={variantClass}
      {...props}
    >
      {children}
    </HeadlessButton>
  );
}

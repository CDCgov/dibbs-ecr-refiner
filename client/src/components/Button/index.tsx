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
  const sharedStyles =
    'm-0 appearance-none cursor-pointer text-center rounded justify-center items-center gap-2 mr-2 px-5 py-3 font-bold leading-none no-underline inline-flex';

  const primaryStyle = classNames(
    sharedStyles,
    'bg-violet-warm-60 hover:bg-violet-warm-70 text-white border-0'
  );

  const secondaryStyle = classNames(
    sharedStyles,
    'bg-white text-violet-warm-60 hover:text-violet-warm-70 hover:border-violet-warm-70 border-violet-warm-60 border-[2px]'
  );
  const tertiaryStyle = classNames(sharedStyles);

  if (href) {
    return (
      <a
        href={href}
        className={classNames(
          {
            [primaryStyle]: variant === 'primary',
            [secondaryStyle]: variant === 'secondary',
            [tertiaryStyle]: variant === 'tertiary',
          },
          className
        )}
      >
        {children}
      </a>
    );
  }

  if (to) {
    const sideEffect = onClick as
      | React.MouseEventHandler<HTMLAnchorElement>
      | undefined;
    return (
      <Link
        onClick={sideEffect}
        to={to}
        className={classNames(
          {
            [primaryStyle]: variant === 'primary',
            [secondaryStyle]: variant === 'secondary',
            [tertiaryStyle]: variant === 'tertiary',
          },
          className
        )}
      >
        {children}
      </Link>
    );
  }

  return (
    <HeadlessButton
      onClick={onClick}
      type={type}
      disabled={disabled}
      className={classNames(
        {
          [primaryStyle]: variant === 'primary',
          [secondaryStyle]: variant === 'secondary',
          [tertiaryStyle]: variant === 'tertiary',
        },
        className
      )}
      {...props}
    >
      {children}
    </HeadlessButton>
  );
}

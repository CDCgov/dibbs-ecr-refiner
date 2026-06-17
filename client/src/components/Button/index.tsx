import { Link } from 'react-router';
import classNames from 'classnames';
import {
  Button as HeadlessButton,
  ButtonProps as HeadlessButtonProps,
} from '@headlessui/react';
import { forwardRef } from 'react';
import { DISABLED_STYLES, VARIANT_STYLES } from './styles';

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'unstyled';

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
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      type = 'button',
      href,
      to,
      onClick,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const variantClass = classNames(
      VARIANT_STYLES[variant],
      { [DISABLED_STYLES]: disabled },
      className
    );

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
        ref={ref}
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
);

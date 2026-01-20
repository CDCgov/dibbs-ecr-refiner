import { Link } from 'react-router';
import {
  ButtonProps as UswdsButtonProps,
  Button as UswdsButton,
} from '@trussworks/react-uswds';
import classNames from 'classnames';

export type ButtonVariant = 'primary' | 'secondary' | 'selected' | 'tertiary';
interface ButtonProps extends Omit<UswdsButtonProps, 'type'> {
  type?: UswdsButtonProps['type'];
  variant?: ButtonVariant;
  to?: string;
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
  to,
  onClick,
  className,
  disabled,
  ...props
}: ButtonProps) {
  if (to) {
    const sideEffect = onClick as
      | React.MouseEventHandler<HTMLAnchorElement>
      | undefined;
    return (
      <Link
        onClick={sideEffect}
        to={to}
        className={classNames('usa-button--outline', className)}
      >
        {children}
      </Link>
    );
  }

  return (
    <UswdsButton
      onClick={onClick}
      type={type}
      disabled={disabled}
      className={className}
      secondary={variant === 'secondary'}
      unstyled={variant === 'tertiary'}
      {...props}
    >
      {children}
    </UswdsButton>
  );
}

import { Link } from 'react-router';
import {
  ButtonProps as UswdsButtonProps,
  Button as UswdsButton,
} from '@trussworks/react-uswds';
import classNames from 'classnames';

interface ButtonProps extends Omit<UswdsButtonProps, 'type'> {
  type?: UswdsButtonProps['type'];
  variant?: 'primary' | 'secondary';
  to?: string;
}

export function Button({
  children,
  variant = 'primary',
  type = 'button',
  to,
  onClick,
  className,
  ...props
}: ButtonProps) {
  const purpleButtonStyles = '!bg-violet-warm-60 hover:!bg-violet-warm-70';

  const styles = classNames('usa-button', className, purpleButtonStyles, {
    'usa-button--secondary': variant === 'secondary',
  });

  if (to) {
    const sideEffect = onClick as
      | React.MouseEventHandler<HTMLAnchorElement>
      | undefined;
    return (
      <Link onClick={sideEffect} to={to} className={styles}>
        {children}
      </Link>
    );
  }

  return (
    <UswdsButton
      secondary={variant === 'secondary'}
      onClick={onClick}
      type={type}
      className="!bg-violet-warm-60 hover:!bg-violet-warm-70"
      {...props}
    >
      {children}
    </UswdsButton>
  );
}

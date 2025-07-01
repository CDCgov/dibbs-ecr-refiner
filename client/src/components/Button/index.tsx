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
  const styles = classNames(className, {
    '!bg-violet-warm-60 hover:!bg-violet-warm-70': variant === 'primary',
    '!bg-white !text-violet-warm-60 !border-violet-warm-60 !border-[2px] !rounded-sm hover:!border-violet-warm-70 hover:!text-violet-warm-70':
      variant === 'secondary',
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
    <UswdsButton onClick={onClick} type={type} className={styles} {...props}>
      {children}
    </UswdsButton>
  );
}

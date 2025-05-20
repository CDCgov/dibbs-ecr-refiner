import classNames from 'classnames';
import { Link } from 'react-router';
import { ButtonProps as UswdsButtonProps } from '@trussworks/react-uswds';
import styles from './button.module.scss';

interface ButtonProps extends UswdsButtonProps {
  variant: 'primary' | 'secondary';
  to?: string;
}

export function Button({
  children,
  variant = 'primary',
  to,
  onClick,
}: ButtonProps) {
  const defaultStyles = 'usa-button';

  const btnClass = classNames(defaultStyles, {
    [styles.btnPrimary]: variant === 'primary',
  });

  if (to) {
    const sideEffect = onClick as
      | React.MouseEventHandler<HTMLAnchorElement>
      | undefined;
    return (
      <Link onClick={sideEffect} to={to} className={btnClass}>
        {children}
      </Link>
    );
  }

  return (
    <button onClick={onClick} className={btnClass}>
      {children}
    </button>
  );
}

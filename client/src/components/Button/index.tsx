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
export const PRIMARY_BUTTON_STYLES =
  '!bg-violet-warm-60 hover:!bg-violet-warm-70';

export const SECONDARY_BUTTON_STYLES =
  '!bg-white !text-violet-warm-60 !border-violet-warm-60 !border-[2px] !rounded-sm hover:!border-violet-warm-70 hover:!text-violet-warm-70';

export const DISABLED_BUTTON_STYLES =
  '!bg-disabled-light !text-disabled-dark hover:!bg-disabled-light !cursor-not-allowed';

export const SELECTED_BUTTON_STYLES =
  'bg-transparent text-black hover:!bg-transparent hover:!text-black active:!bg-transparent active:!text-black';

export const TERTIARY_BUTTON_STYLES =
  '!bg-transparent !text-blue-cool-60 hover:!underline hover:cursor-pointer !p-0 !m-0';

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
  const styles = classNames(
    className,
    disabled
      ? DISABLED_BUTTON_STYLES
      : {
          [PRIMARY_BUTTON_STYLES]: variant === 'primary',
          [SECONDARY_BUTTON_STYLES]: variant === 'secondary',
          [SELECTED_BUTTON_STYLES]: variant === 'selected',
          [TERTIARY_BUTTON_STYLES]: variant === 'tertiary',
        }
  );
  if (to) {
    const sideEffect = onClick as
      | React.MouseEventHandler<HTMLAnchorElement>
      | undefined;
    return (
      <Link
        onClick={sideEffect}
        to={to}
        className={classNames('usa-button', styles)}
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
      className={styles}
      {...props}
    >
      {children}
    </UswdsButton>
  );
}

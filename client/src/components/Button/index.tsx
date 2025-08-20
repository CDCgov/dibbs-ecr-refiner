import { Link } from 'react-router';
import {
  ButtonProps as UswdsButtonProps,
  Button as UswdsButton,
} from '@trussworks/react-uswds';
import classNames from 'classnames';

interface ButtonProps extends Omit<UswdsButtonProps, 'type'> {
  type?: UswdsButtonProps['type'];
  variant?: 'primary' | 'secondary' | 'disabled' | 'selected';
  to?: string;
}

/**
 * Button component supporting multiple variants and behaviors,
 * including primary, secondary, and disabled styles, with optional
 * routing functionality.
 *
 * @param {Object} props - The properties for the Button component.
 * @param {React.ReactNode} props.children - The content to be displayed inside the button.
 * @param {'primary' | 'secondary' | 'disabled' | 'selected'} [props.variant='primary'] - The variant style of the button.
 * @param {string} [props.type='button'] - The type of the button (e.g., 'button', 'submit').
 * @param {string} [props.to] - The route path for the button if it should act as a link.
 * @param {React.MouseEventHandler<HTMLButtonElement | HTMLAnchorElement>} [props.onClick] - The click event handler for the button or link.
 * @param {string} [props.className] - Additional class names to style the button.
 * @param {Object} [props.props] - Additional properties passed to the underlying button or link component.
 *
 * @returns {React.ReactElement<ButtonProps>} - The rendered Button component.
 */
export function Button({
  children,
  variant = 'primary',
  type = 'button',
  to,
  onClick,
  className,
  ...props
}: ButtonProps): React.ReactElement<ButtonProps> {
  const styles = classNames(className, {
    '!bg-violet-warm-60 hover:!bg-violet-warm-70': variant === 'primary',
    '!bg-white !text-violet-warm-60 !border-violet-warm-60 !border-[2px] !rounded-sm hover:!border-violet-warm-70 hover:!text-violet-warm-70':
      variant === 'secondary',
    '!bg-disabled-light !text-disabled-dark hover:!bg-disabled-light !cursor-not-allowed':
      variant === 'disabled',
    'bg-transparent text-black hover:!bg-transparent hover:!text-black active:!bg-transparent active:!text-black':
      variant === 'selected',
  });

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
    <UswdsButton onClick={onClick} type={type} className={styles} {...props}>
      {children}
    </UswdsButton>
  );
}

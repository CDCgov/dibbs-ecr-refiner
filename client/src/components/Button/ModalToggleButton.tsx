import {
  ModalToggleButtonProps as UswdsModalButtonProps,
  ModalToggleButton as UswdsModalToggleButton,
} from '@trussworks/react-uswds';
import {
  ButtonVariant,
  DISABLED_BUTTON_STYLES,
  PRIMARY_BUTTON_STYLES,
  SECONDARY_BUTTON_STYLES,
  SELECTED_BUTTON_STYLES,
  TERTIARY_BUTTON_STYLES,
} from '.';
import classNames from 'classnames';
import { JSX } from 'react';

interface ModalButtonProps extends UswdsModalButtonProps {
  variant?: ButtonVariant;
  className?: string;
}
export function ModalToggleButton({
  children,
  modalRef,
  opener,
  closer,
  variant,
  className,
  disabled,
  ...props
}: ModalButtonProps & JSX.IntrinsicElements['button']) {
  let buttonStyles;
  if (disabled) {
    buttonStyles = DISABLED_BUTTON_STYLES;
  } else {
    switch (variant) {
      case 'secondary':
        buttonStyles = SECONDARY_BUTTON_STYLES;
        break;

      case 'disabled':
        buttonStyles = DISABLED_BUTTON_STYLES;
        break;

      case 'selected':
        buttonStyles = SELECTED_BUTTON_STYLES;
        break;

      case 'tertiary':
        buttonStyles = TERTIARY_BUTTON_STYLES;
        break;
      default:
        buttonStyles = PRIMARY_BUTTON_STYLES;
    }
  }

  return (
    <UswdsModalToggleButton
      className={classNames(buttonStyles, className)}
      modalRef={modalRef}
      opener={opener}
      closer={closer}
      disabled={disabled}
      {...props}
    >
      {children}
    </UswdsModalToggleButton>
  );
}

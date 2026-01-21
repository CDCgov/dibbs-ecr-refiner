import {
  ModalToggleButtonProps as UswdsModalButtonProps,
  ModalToggleButton as UswdsModalToggleButton,
} from '@trussworks/react-uswds';
import { ButtonVariant } from '.';
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
  return (
    <UswdsModalToggleButton
      className={className}
      modalRef={modalRef}
      opener={opener}
      closer={closer}
      disabled={disabled}
      secondary={variant === 'secondary'}
      unstyled={variant === 'tertiary'}
      {...props}
    >
      {children}
    </UswdsModalToggleButton>
  );
}

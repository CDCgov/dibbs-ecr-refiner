import { ModalRef } from '@trussworks/react-uswds';
import { useRef } from 'react';

import { TurnOnModal } from '../modals/TurnOnModal';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';

interface TurnOnButtonsProps {
  handleActivation: () => void;
  disabled?: boolean;
}
export function TurnOnButtons({
  handleActivation,
  disabled,
}: TurnOnButtonsProps) {
  const activateRef = useRef<ModalRef>(null);

  return (
    <div>
      <ModalToggleButton
        modalRef={activateRef}
        opener
        variant="secondary"
        disabled={disabled}
      >
        Turn on configuration
      </ModalToggleButton>

      <TurnOnModal modalRef={activateRef} handleActivation={handleActivation} />
    </div>
  );
}

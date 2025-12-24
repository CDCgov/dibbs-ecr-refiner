import { ModalRef, ModalToggleButton } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { useRef } from 'react';
import { SECONDARY_BUTTON_STYLES } from '../../../../components/Button';
import { TurnOffModal } from '../modals/TurnOffModal';

interface TurnOffButtonsProps {
  handleDeactivation: () => void;
  disabled?: boolean;
}
export function TurnOffButtons({ handleDeactivation, disabled }: TurnOffButtonsProps) {
  const deactivateRef = useRef<ModalRef>(null);

  return (
    <div>
      <ModalToggleButton
        modalRef={deactivateRef}
        opener
        className={classNames('self-start', SECONDARY_BUTTON_STYLES)}
        disabled={disabled}
      >
        Turn off current version
      </ModalToggleButton>

      <TurnOffModal
        modalRef={deactivateRef}
        handleDeactivation={handleDeactivation}
      />
    </div>
  );
}

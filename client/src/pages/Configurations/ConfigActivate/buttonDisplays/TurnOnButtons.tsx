import { ModalRef, ModalToggleButton } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { useRef } from 'react';
import { SECONDARY_BUTTON_STYLES } from '../../../../components/Button';
import { TurnOnModal } from '../modals/TurnOnModal';

interface TurnOnButtonsProps {
  handleActivation: () => void;
}
export function TurnOnButtons({ handleActivation }: TurnOnButtonsProps) {
  const activateRef = useRef<ModalRef>(null);

  return (
    <div>
      <ModalToggleButton
        modalRef={activateRef}
        opener
        className={classNames('self-start', SECONDARY_BUTTON_STYLES)}
      >
        Turn on configuration
      </ModalToggleButton>

      <TurnOnModal modalRef={activateRef} handleActivation={handleActivation} />
    </div>
  );
}

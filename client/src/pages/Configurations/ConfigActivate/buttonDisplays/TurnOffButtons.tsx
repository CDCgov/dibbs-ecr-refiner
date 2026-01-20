import { ModalRef } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { useRef } from 'react';
import { TurnOffModal } from '../modals/TurnOffModal';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';

interface TurnOffButtonsProps {
  handleDeactivation: () => void;
  disabled: boolean;
}
export function TurnOffButtons({
  handleDeactivation,
  disabled,
}: TurnOffButtonsProps) {
  const deactivateRef = useRef<ModalRef>(null);

  return (
    <div>
      <ModalToggleButton
        modalRef={deactivateRef}
        opener
        className={classNames('self-start')}
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

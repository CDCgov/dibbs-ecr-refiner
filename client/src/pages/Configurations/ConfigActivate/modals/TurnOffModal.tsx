import { ModalRef, ModalToggleButton } from '@trussworks/react-uswds';
import { Button, SECONDARY_BUTTON_STYLES } from '../../../../components/Button';
import { GenericModal } from './GenericModal';
import { RefObject } from 'react';

interface TurnOffModal {
  handleDeactivation: () => void;
  modalRef: RefObject<ModalRef | null>;
}

export function TurnOffModal({ modalRef, handleDeactivation }: TurnOffModal) {
  return (
    <GenericModal
      modalRef={modalRef}
      title="Turn off current version"
      body={
        <div>
          <p id="deactivation-confirmation-modal-text" className="my-6">
            You’re about to stop the current version. No versions will be
            running until you turn on a new one. Do you want to continue?
          </p>
        </div>
      }
      footer={
        <div>
          <ModalToggleButton
            modalRef={modalRef}
            closer
            className={SECONDARY_BUTTON_STYLES}
          >
            Cancel
          </ModalToggleButton>
          <Button onClick={() => handleDeactivation()}>Yes, turn off</Button>
        </div>
      }
    />
  );
}

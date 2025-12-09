import { ModalRef, ModalToggleButton } from '@trussworks/react-uswds';
import { GenericModal } from './GenericModal';
import { Button, SECONDARY_BUTTON_STYLES } from '../../../../components/Button';
import { RefObject } from 'react';

interface SwitchActivationModal {
  curVersion: number;
  activeVersion: number | null;
  handleActivation: () => void;
  modalRef: RefObject<ModalRef | null>;
}
export function SwitchActivationModal({
  modalRef,
  curVersion,
  activeVersion,
  handleActivation,
}: SwitchActivationModal) {
  return (
    <GenericModal
      modalRef={modalRef}
      title={`Switch to Version ${curVersion}`}
      body={
        <div>
          <p id="activation-confirmation-modal-text" className="my-6">
            You're about to stop Version {activeVersion} and start Version{' '}
            {curVersion}
          </p>
          <p>
            The eCR pipeline will begin using Version {curVersion}{' '}
            <b>immediately</b>
          </p>
          <p>Do you want to continue?</p>
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
          <Button onClick={() => handleActivation()}>
            Yes, switch to Version {curVersion}
          </Button>
        </div>
      }
    />
  );
}

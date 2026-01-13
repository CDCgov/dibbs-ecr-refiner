import { ModalRef } from '@trussworks/react-uswds';
import { GenericModal } from './GenericModal';
import { Button } from '../../../../components/Button';
import { RefObject } from 'react';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';

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
            <span className="font-bold">immediately</span>
          </p>
          <p>Do you want to continue?</p>
        </div>
      }
      footer={
        <div>
          <ModalToggleButton modalRef={modalRef} closer variant="secondary">
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

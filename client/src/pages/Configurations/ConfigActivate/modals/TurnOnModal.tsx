import { RefObject } from 'react';
import { Button } from '../../../../components/Button';
import { GenericModal } from './GenericModal';
import { ModalRef } from '@trussworks/react-uswds';

interface TurnOnModal {
  handleActivation: () => void;
  modalRef: RefObject<ModalRef | null>;
}

export function TurnOnModal({ modalRef, handleActivation }: TurnOnModal) {
  return (
    <GenericModal
      modalRef={modalRef}
      title="Turn on configuration?"
      body={
        <div>
          <ul>
            <li>
              Refiner will <span className="text-bold">immediately</span> start
              to refine the eCR's
            </li>
            <li>
              You <span className="text-bold">cannot</span> edit this version
              after you activate it
            </li>
          </ul>
          <p id="activation-confirmation-modal-text" className="my-6">
            Are you sure you want to turn on the configuration?
          </p>
        </div>
      }
      footer={
        <Button onClick={() => handleActivation()}>
          Yes, turn on configuration
        </Button>
      }
    />
  );
}

import { useState } from 'react';
import { Button } from '../../../components/Button';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '../../../components/Modal';

interface TurnOffConfigButtonProps {
  handleDeactivation: () => void;
  disabled: boolean;
}

export function TurnOffConfigButton({
  handleDeactivation,
  disabled,
}: TurnOffConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <TurnOffConfigModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        handleDeactivation={handleDeactivation}
      />
      <h3 className="mt-6 mb-4 text-lg font-bold">Option 2</h3>
      <div className="flex flex-row items-center gap-2">
        <Button
          onClick={() => setIsOpen(true)}
          variant="secondary"
          className="self-start"
          disabled={disabled}
        >
          Turn off configuration
        </Button>
        <p>
          Stop the current version. No version will be active until you turn one
          on
        </p>
      </div>
    </div>
  );
}

type TurnOffConfigModalProps = Pick<
  TurnOffConfigButtonProps,
  'handleDeactivation'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function TurnOffConfigModal({
  isOpen,
  onClose,
  handleDeactivation,
}: TurnOffConfigModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>Turn off current version</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p id="deactivation-confirmation-modal-text" className="my-6">
          You're about to stop the current version. No versions will be running
          until you turn on a new one. Do you want to continue?
        </p>
      </ModalBody>

      <ModalFooter>
        <Button onClick={onClose} variant="secondary">
          Cancel
        </Button>
        <Button onClick={() => handleDeactivation()}>Yes, turn off</Button>
      </ModalFooter>
    </Modal>
  );
}

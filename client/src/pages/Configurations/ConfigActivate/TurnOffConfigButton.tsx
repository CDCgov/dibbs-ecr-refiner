import { useState } from 'react';
import { Button } from '@components/Button';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Spinner } from '@components/Spinner';

interface TurnOffConfigButtonProps {
  handleDeactivation: () => void;
  disabled: boolean;
  isLoading: boolean;
  grouped?: boolean;
}

export function TurnOffConfigButton({
  handleDeactivation,
  disabled,
  isLoading,
}: TurnOffConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <TurnOffConfigModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        handleDeactivation={handleDeactivation}
        isLoading={isLoading}
      />
        <Button
          onClick={() => setIsOpen(true)}
          variant="secondary"
          className="self-start"
          disabled={disabled}
        >
          Deactivate
        </Button>
    </div>
  );
}

type TurnOffConfigModalProps = Pick<
  TurnOffConfigButtonProps,
  'handleDeactivation' | 'isLoading'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function TurnOffConfigModal({
  isOpen,
  onClose,
  handleDeactivation,
  isLoading,
}: TurnOffConfigModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>Turn off current version</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p>
          You're about to stop the current version. No versions will be running
          until you turn on a new one. Do you want to continue?
        </p>
      </ModalBody>

      <ModalFooter align="right">
        {isLoading ? null : (
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
        )}
        <Button
          className="min-w-33"
          onClick={() => handleDeactivation()}
          disabled={isLoading}
        >
          {isLoading ? <Spinner size="20px" /> : 'Yes, turn off'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

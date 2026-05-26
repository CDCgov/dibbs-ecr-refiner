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
  grouped = false,
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
      <div className="flex flex-row items-center gap-1">
        <Button
          onClick={() => setIsOpen(true)}
          variant={grouped ? 'secondary' : 'primary'}
          className="self-start"
          disabled={disabled}
        >
          {grouped ? 'Turn off configuration' : 'Turn off current version'}
        </Button>
        {grouped ? (
          <p>
            Stop the current version. No version will be active until you turn
            one on
          </p>
        ) : null}
      </div>
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

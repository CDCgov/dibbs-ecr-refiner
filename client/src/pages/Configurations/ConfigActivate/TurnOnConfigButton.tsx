import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';

interface TurnOnConfigButtonProps {
  handleActivation: () => void;
  disabled: boolean;
  isLoading: boolean;
}
export function TurnOnConfigButton({
  handleActivation,
  disabled,
  isLoading,
}: TurnOnConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <Button
        onClick={() => setIsOpen(true)}
        variant="secondary"
        disabled={disabled}
      >
        Turn on configuration
      </Button>

      <TurnOnConfigModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        handleActivation={handleActivation}
        isLoading={isLoading}
      />
    </div>
  );
}

type TurnOnConfigModalProps = Pick<
  TurnOnConfigButtonProps,
  'handleActivation' | 'isLoading'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function TurnOnConfigModal({
  isOpen,
  onClose,
  handleActivation,
  isLoading,
}: TurnOnConfigModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>Turn on configuration?</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <ul className="list-inside">
            <li>
              Refiner will <span className="text-bold">immediately</span> start
              to refine the eCRs
            </li>
            <li>
              You <span className="text-bold">cannot</span> edit this version
              after you activate it
            </li>
          </ul>
          <p>Are you sure you want to turn on the configuration?</p>
        </div>
      </ModalBody>
      <ModalFooter align="right">
        <Button
          className="min-w-58.75"
          onClick={() => handleActivation()}
          disabled={isLoading}
        >
          {isLoading ? <Spinner size="20px" /> : 'Yes, turn on configuration'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

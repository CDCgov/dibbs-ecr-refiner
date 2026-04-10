import { useState } from 'react';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Button } from '@components/Button';

interface TurnOnConfigButtonProps {
  handleActivation: () => void;
  disabled: boolean;
}
export function TurnOnConfigButton({
  handleActivation,
  disabled,
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
      />
    </div>
  );
}

type TurnOnConfigModalProps = Pick<
  TurnOnConfigButtonProps,
  'handleActivation'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function TurnOnConfigModal({
  isOpen,
  onClose,
  handleActivation,
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
        <Button onClick={() => handleActivation()}>
          Yes, turn on configuration
        </Button>
      </ModalFooter>
    </Modal>
  );
}

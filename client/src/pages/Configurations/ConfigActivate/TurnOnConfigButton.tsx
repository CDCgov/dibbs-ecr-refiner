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
  handleActivation: () => Promise<void>;
  disabled: boolean;
  isLoading: boolean;
  hasPrimaryCondition: boolean;
}
export function TurnOnConfigButton({
  handleActivation,
  disabled,
  isLoading,
  hasPrimaryCondition,
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
        hasPrimaryCondition={hasPrimaryCondition}
      />
    </div>
  );
}

type TurnOnConfigModalProps = Pick<
  TurnOnConfigButtonProps,
  'handleActivation' | 'isLoading' | 'hasPrimaryCondition'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function TurnOnConfigModal({
  isOpen,
  onClose,
  handleActivation,
  isLoading,
  hasPrimaryCondition,
}: TurnOnConfigModalProps) {
  const isZeroCodeSet = !hasPrimaryCondition;

  const modalTitle = isZeroCodeSet
    ? 'Activate Zero-Code-Set Configuration?'
    : 'Turn on configuration?';

  const modalBody = isZeroCodeSet ? (
    <div className="flex flex-col gap-4">
      <p>
        This configuration has no primary condition. Activating it will cause
        the refiner to skip all code-set mapping loops. Are you sure you want to
        proceed?
      </p>
    </div>
  ) : (
    <div className="flex flex-col gap-4">
      <ul className="list-inside">
        <li>
          Refiner will <span className="text-bold">immediately</span> start to
          refine the eCRs
        </li>
        <li>
          You <span className="text-bold">cannot</span> edit this version after
          you activate it
        </li>
      </ul>
      <p>Are you sure you want to turn on the configuration?</p>
    </div>
  );

  const footerButtons = isZeroCodeSet ? (
    <>
      <Button
        className="mr-2 min-w-58.75"
        onClick={onClose}
        disabled={isLoading}
        variant="tertiary"
      >
        Cancel
      </Button>
      <Button
        className="min-w-58.75"
        onClick={() => handleActivation()}
        disabled={isLoading}
      >
        {isLoading ? <Spinner size="20px" /> : 'Activate'}
      </Button>
    </>
  ) : (
    <Button
      className="min-w-58.75"
      onClick={() => handleActivation()}
      disabled={isLoading}
    >
      {isLoading ? <Spinner size="20px" /> : 'Yes, turn on configuration'}
    </Button>
  );

  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>{modalTitle}</ModalTitle>
      </ModalHeader>
      <ModalBody>{modalBody}</ModalBody>
      <ModalFooter align="right">{footerButtons}</ModalFooter>
    </Modal>
  );
}

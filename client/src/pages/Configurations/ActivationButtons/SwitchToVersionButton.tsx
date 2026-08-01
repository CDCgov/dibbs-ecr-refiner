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
import { ActivateButton } from './ActivateButton';

interface SwitchToVersionButtonProps {
  handleActivation: () => void;
  curVersion: number;
  activeVersion: number | null;
  isLoading: boolean;
  disabled: boolean;
}
export function SwitchToVersionButton({
  handleActivation,
  curVersion,
  activeVersion,
  isLoading,
  disabled,
}: SwitchToVersionButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <ActivateButton onClick={() => setIsOpen(true)} disabled={disabled} />
      <SwitchToVersionModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        activeVersion={activeVersion}
        curVersion={curVersion}
        handleActivation={handleActivation}
        isLoading={isLoading}
      />
    </div>
  );
}

type SwitchToVersionModalProps = Pick<
  SwitchToVersionButtonProps,
  'curVersion' | 'activeVersion' | 'handleActivation' | 'isLoading'
> & {
  isOpen: boolean;
  onClose: () => void;
};

function SwitchToVersionModal({
  isOpen,
  onClose,
  curVersion,
  activeVersion,
  handleActivation,
  isLoading,
}: SwitchToVersionModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>{`Switch to Version ${curVersion}`}</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <p>
            You're about to stop Version {activeVersion} and start Version{' '}
            {curVersion}
          </p>
          <p>
            The eCR pipeline will begin using Version {curVersion}{' '}
            <span className="font-bold">immediately</span>
          </p>
          <p>Do you want to continue?</p>
        </div>
      </ModalBody>
      <ModalFooter align="right">
        {isLoading ? null : (
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
        )}
        <Button
          className="min-w-55"
          onClick={() => handleActivation()}
          disabled={isLoading}
        >
          {isLoading ? (
            <Spinner size="20px" />
          ) : (
            `Yes, switch to Version ${curVersion}`
          )}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

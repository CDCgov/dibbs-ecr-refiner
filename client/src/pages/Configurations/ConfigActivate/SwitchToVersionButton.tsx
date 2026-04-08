import { useState } from 'react';
import { Button } from '../../../components/Button';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '../../../components/Modal';

interface SwitchToVersionButtonProps {
  handleActivation: () => void;
  curVersion: number;
  activeVersion: number | null;
}
export function SwitchToVersionButton({
  handleActivation,
  curVersion,
  activeVersion,
}: SwitchToVersionButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <h3 className="mb-4 text-lg font-bold">Option 1</h3>
      <div className="flex flex-row items-center gap-2">
        <Button onClick={() => setIsOpen(true)} className="self-start">
          Switch to version {curVersion}
        </Button>
        <p>
          Safely replace the current version with this one — it will begin
          processing immediately
        </p>
      </div>
      <SwitchToVersionModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        activeVersion={activeVersion}
        curVersion={curVersion}
        handleActivation={handleActivation}
      />
    </div>
  );
}

type SwitchToVersionModalProps = Pick<
  SwitchToVersionButtonProps,
  'curVersion' | 'activeVersion' | 'handleActivation'
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
}: SwitchToVersionModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top">
      <ModalHeader>
        <ModalTitle>{`Switch to Version ${curVersion}`}</ModalTitle>
      </ModalHeader>
      <ModalBody>
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
      </ModalBody>
      <ModalFooter>
        <div>
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
          <Button onClick={() => handleActivation()}>
            Yes, switch to Version {curVersion}
          </Button>
        </div>
      </ModalFooter>
    </Modal>
  );
}

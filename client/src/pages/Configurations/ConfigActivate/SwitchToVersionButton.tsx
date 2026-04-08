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
  grouped?: boolean;
}
export function SwitchToVersionButton({
  handleActivation,
  curVersion,
  activeVersion,
  grouped = false,
}: SwitchToVersionButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <div className="flex flex-row items-center gap-1">
        <Button
          variant={grouped ? 'primary' : 'secondary'}
          onClick={() => setIsOpen(true)}
          className="self-start"
        >
          Switch to version {curVersion}
        </Button>
        {grouped ? (
          <p>
            Safely replace the current version with this one — it will begin
            processing immediately
          </p>
        ) : null}
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

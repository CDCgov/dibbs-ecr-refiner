import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';

interface ApplyUpdatesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

export function ApplyUpdatesModal({
  isOpen,
  onClose,
  onConfirm,
  isLoading = false,
}: ApplyUpdatesModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="top" maxWidth="xl">
      <ModalHeader>
        <ModalTitle font="merriweather">Create draft?</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p>
          This will create a draft with the latest TES codes for the selected
          configuration(s).
        </p>
        <div className="border-blue-30v bg-blue-5v mt-3 border-l-4 p-3">
          <p className="mb-1 text-sm font-bold text-blue-900">Note:</p>
          <p className="text-sm">
            To use the latest TES release live, activate this draft once the
            update is complete.
          </p>
        </div>
      </ModalBody>
      <ModalFooter align="left">
        <Button variant="primary" onClick={onConfirm} disabled={isLoading}>
          {isLoading ? <Spinner size={16} color="#fff" /> : 'Yes, create draft'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

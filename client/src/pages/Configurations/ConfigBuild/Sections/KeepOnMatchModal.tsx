import { Modal, ModalHeader, ModalTitle, ModalBody } from '@components/Modal';

interface KeepOnMatchModalProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export function KeepOnMatchModal({ isOpen, setIsOpen }: KeepOnMatchModalProps) {
  return (
    <Modal open={isOpen} onClose={() => setIsOpen(false)}>
      <ModalHeader>
        <ModalTitle>Narrative data</ModalTitle>
        <p className="italic">
          Choose how the Refiner should handle the narrative data within each
          section.
        </p>
      </ModalHeader>
      <ModalBody>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <span className="font-semibold">Keep original</span>: if you'd like
            to keep the original narrative data in this section in the refined
            output
          </li>
          <li>
            <span className="font-semibold">Keep on match</span>: if you'd like
            to keep the original narrative data only if a matching code is found
            when refining the coded data for this section
          </li>
          <li>
            <span className="font-semibold">Reconstruct</span>: if you'd like to
            reconstruct the narrative data in this section from the refined
            coded data (only available if coded data is set to
            &quot;Refine&quot;)
          </li>
          <li>
            <span className="font-semibold">Exclude</span>: if you'd like to
            remove the narrative data for this section in its entirety
          </li>
        </ul>
      </ModalBody>
    </Modal>
  );
}

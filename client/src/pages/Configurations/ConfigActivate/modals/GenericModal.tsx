import {
  Modal,
  ModalFooter,
  ModalHeading,
  ModalRef,
} from '@trussworks/react-uswds';
import { RefObject } from 'react';

interface ActivationUpdateModalProps {
  modalRef: RefObject<ModalRef | null>;
  title: string;
  body: React.ReactNode;
  footer: React.ReactNode;
}
export function GenericModal({
  modalRef,
  title,
  body,
  footer,
}: ActivationUpdateModalProps) {
  return (
    <Modal
      id="activation-confirmation-modal"
      className="max-w-140! p-10 align-top!"
      ref={modalRef}
      aria-labelledby="activation-confirmation-modal-heading"
      aria-describedby="activation-confirmation-modal-text"
    >
      <ModalHeading id="activation-confirmation-modal-heading">
        <div className="mb-6">{title}</div>
      </ModalHeading>
      {body}
      <ModalFooter className="flex justify-end">{footer}</ModalFooter>
    </Modal>
  );
}

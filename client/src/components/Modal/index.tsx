import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
} from '@headlessui/react';
import { Button } from '../Button';
import { Icon } from '@trussworks/react-uswds';
import { createContext, useContext } from 'react';

type ModalContextValue = {
  onClose: () => void;
};

const ModalContext = createContext<ModalContextValue | null>(null);

function useModalContext() {
  const ctx = useContext(ModalContext);
  if (!ctx) {
    throw new Error('Modal components must be used within <Modal>');
  }
  return ctx;
}

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

function Modal({ open, onClose, children }: ModalProps) {
  return (
    <ModalContext.Provider value={{ onClose }}>
      <Dialog open={open} onClose={onClose} unmount>
        <DialogBackdrop className="fixed inset-0 bg-black/60" />
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="bg-base-dark/70 fixed inset-0" aria-hidden="true" />
          <DialogPanel className="border-base-lighter relative z-50 w-full max-w-lg rounded-sm border bg-white text-left shadow-lg">
            {open && <div>{children}</div>}
          </DialogPanel>
        </div>
      </Dialog>
    </ModalContext.Provider>
  );
}

interface ModalContentProps {
  children: React.ReactNode;
}

function ModalContent({ children }: ModalContentProps) {
  const { onClose } = useModalContext();

  return (
    <div className='pb-5'>
      <div className="relative p-6">
        <Button
          aria-label="Close this window"
          onClick={onClose}
          className="absolute top-4 right-4 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
        >
          <Icon.Close size={4} aria-hidden />
        </Button>
      </div>
      <div className="mx-auto flex w-full max-w-md justify-center">
        <div className="flex flex-col gap-4 text-left">{children}</div>
      </div>
    </div>
  );
}

function ModalTitle({ children }: ModalContentProps) {
  return (
    <DialogTitle className="font-merriweather text-gray-90 text-3xl font-bold">
      {children}
    </DialogTitle>
  );
}

export { Modal, ModalContent, ModalTitle };

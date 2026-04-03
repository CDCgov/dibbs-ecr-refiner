import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
} from '@headlessui/react';
import { Icon } from '@trussworks/react-uswds';
import { createContext, useContext } from 'react';
import classNames from 'classnames';

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
  position?: 'center' | 'top';
  className?: string;
}

function Modal({
  open,
  onClose,
  children,
  position = 'center',
  className,
}: ModalProps) {
  return (
    <ModalContext.Provider value={{ onClose }}>
      <Dialog open={open} onClose={onClose} unmount>
        <DialogBackdrop className="fixed inset-0 bg-black/60" />

        <div
          className={classNames('fixed inset-0 z-50 flex justify-center p-4', {
            'items-center': position === 'center',
            'items-start': position === 'top',
          })}
        >
          <div className="bg-base-dark/70 fixed inset-0" aria-hidden="true" />

          <DialogPanel
            className={classNames(
              'border-base-lighter relative z-50 w-full max-w-lg rounded-sm border bg-white shadow-lg',
              className
            )}
          >
            {children}
          </DialogPanel>
        </div>
      </Dialog>
    </ModalContext.Provider>
  );
}

interface ModalSectionProps {
  children: React.ReactNode;
  className?: string;
}

function ModalHeader({ children }: ModalSectionProps) {
  const { onClose } = useModalContext();

  return (
    <div className="relative px-6 pt-6 pb-4">
      <button
        aria-label="Close this window"
        onClick={onClose}
        className="absolute top-4 right-4 rounded hover:cursor-pointer"
      >
        <Icon.Close
          className="text-gray-500 hover:text-gray-900"
          size={4}
          aria-hidden
        />
      </button>

      <div className="mx-auto mt-6 w-full pr-10 pl-6">{children}</div>
    </div>
  );
}

function ModalTitle({ children, className }: ModalSectionProps) {
  return (
    <DialogTitle
      className={classNames(
        'font-merriweather text-gray-90 text-3xl font-bold',
        className
      )}
    >
      {children}
    </DialogTitle>
  );
}

function ModalBody({ children, className }: ModalSectionProps) {
  return (
    <div className={classNames('mx-auto w-full max-w-md px-6 pb-6', className)}>
      <div className="flex flex-col gap-4 text-left">{children}</div>
    </div>
  );
}

function ModalFooter({ children, className }: ModalSectionProps) {
  return (
    <div className={classNames('py-4', className)}>
      <div className="mx-auto flex w-full max-w-md gap-3 pl-6">{children}</div>
    </div>
  );
}

export { Modal, ModalHeader, ModalTitle, ModalBody, ModalFooter };

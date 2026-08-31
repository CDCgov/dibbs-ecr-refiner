import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
} from '@headlessui/react';
import { useEffect } from 'react';
import classNames from 'classnames';
import { CloseIcon } from '@components/Icons/CloseIcon';
import { useModalContext } from './ModalContext';
import { ModalProvider } from './ModalProvider';

type WidthSettings = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  position?: 'center' | 'top';
  maxWidth?: WidthSettings;
  className?: string;
}
/**
 * This is a generic Modal component.
 * @example
 * function MyCustomModal() {
    const [isOpen, setIsOpen] = useState(false);

    return (
      <Modal open={isOpen} onClose={() => setIsOpen(false)}>
        <ModalHeader>
          <ModalTitle>My Custom Modal</ModalTitle>
        </ModalHeader>
          <ModalBody>
            <p>Content goes here</p>
          </ModalBody>
          <ModalFooter>
            <Button onClick={() => setIsOpen(false)}>Close the modal</Button>
          </ModalFooter>
      </Modal>
    );
  }
 */
function Modal({
  open,
  onClose,
  children,
  position = 'top',
  maxWidth = 'lg',
  className,
}: ModalProps) {
  const { setIsModalOpen } = useModalContext();

  useEffect(() => {
    setIsModalOpen(open);
    return () => setIsModalOpen(false);
  }, [open, setIsModalOpen]);

  return (
    <ModalProvider>
      <Dialog open={open} onClose={onClose} unmount>
        <DialogBackdrop className="z-modal-backdrop fixed inset-0 bg-black/60" />

        <div
          className={classNames(
            'z-modal-backdrop fixed inset-0 flex justify-center overflow-auto pt-15',
            {
              'items-center': position === 'center',
              'items-start': position === 'top',
            }
          )}
        >
          <DialogPanel
            className={classNames(
              `border-base-lighter z-modal-content relative w-full max-w-${maxWidth} rounded-sm border bg-white p-6 shadow-lg`,
              className
            )}
          >
            <ModalCloseButton onClose={onClose} />
            {children}
          </DialogPanel>
        </div>
      </Dialog>
    </ModalProvider>
  );
}

function ModalCloseButton({ onClose }: { onClose: () => void }) {
  return (
    <button
      aria-label="Close this window"
      onClick={onClose}
      className="absolute top-4 right-4 rounded hover:cursor-pointer"
    >
      <CloseIcon className="fill-gray-500 hover:fill-gray-900" />
    </button>
  );
}

interface ModalSectionProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: WidthSettings;
}

function ModalHeader({ children }: ModalSectionProps) {
  return <div className="mx-auto mt-6 w-full pr-10 pb-6 pl-6">{children}</div>;
}

function ModalTitle({ children }: ModalSectionProps) {
  return (
    <DialogTitle className="font-public-sans text-gray-90 text-3xl font-bold">
      {children}
    </DialogTitle>
  );
}

function ModalBody({ children, className }: ModalSectionProps) {
  return (
    <div className={classNames('px-6 pb-6', className)}>
      <div className="flex flex-col gap-4 text-left">{children}</div>
    </div>
  );
}

interface ModalFooterProps extends ModalSectionProps {
  align?: 'left' | 'right' | 'between' | 'center';
}

function ModalFooter({
  children,
  className,
  align = 'left',
}: ModalFooterProps) {
  return (
    <div className={className}>
      <div
        className={classNames(`flex w-full gap-3 px-6`, {
          'justify-start': align === 'left',
          'justify-end': align === 'right',
          'justify-center': align === 'center',
          'justify-between': align === 'between',
        })}
      >
        {children}
      </div>
    </div>
  );
}

export { Modal, ModalHeader, ModalTitle, ModalBody, ModalFooter };

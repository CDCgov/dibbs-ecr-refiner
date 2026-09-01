import { createContext, useContext } from 'react';

interface ModalContextValue {
  isModalOpen: boolean;
  setIsModalOpen: (open: boolean) => void;
}
export const ModalContext = createContext<ModalContextValue | null>(null);

export function useModalContext() {
  const ctx = useContext(ModalContext);
  if (!ctx) {
    throw new Error('Modal components must be used within <Modal>');
  }
  return ctx;
}

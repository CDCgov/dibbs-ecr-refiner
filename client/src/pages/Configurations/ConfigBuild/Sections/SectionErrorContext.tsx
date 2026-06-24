import { createContext } from 'react';

interface SectionErrorContextValue {
  errorSectionCode: string | null;
  setError: (code: string) => void;
  clearError: () => void;
}

export const SectionErrorContext =
  createContext<SectionErrorContextValue | null>(null);

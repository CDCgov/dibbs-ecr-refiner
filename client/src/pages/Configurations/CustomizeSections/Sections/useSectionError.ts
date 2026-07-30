import { useContext } from 'react';
import { SectionErrorContext } from './SectionErrorContext';

export function useSectionError() {
  const ctx = useContext(SectionErrorContext);
  if (!ctx)
    throw new Error(
      'useSectionError must be used within a SectionErrorProvider'
    );
  return ctx;
}

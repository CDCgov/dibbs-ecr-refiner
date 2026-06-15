import { createContext, useContext, useState, useEffect } from 'react';

interface SectionErrorContextValue {
  errorSectionCode: string | null;
  setError: (code: string) => void;
  clearError: () => void;
}

const SectionErrorContext = createContext<SectionErrorContextValue | null>(
  null
);

export function SectionErrorProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [errorSectionCode, setErrorSectionCode] = useState<string | null>(null);

  useEffect(() => {
    const handleGlobalClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      // We check if the click was inside an element with [data-error-trigger]
      // or any of its children.
      if (!target.closest('[data-error-trigger]')) {
        setErrorSectionCode(null);
      }
    };

    window.addEventListener('click', handleGlobalClick);
    return () => window.removeEventListener('click', handleGlobalClick);
  }, []);

  return (
    <SectionErrorContext.Provider
      value={{
        errorSectionCode,
        setError: (code) => setErrorSectionCode(code),
        clearError: () => setErrorSectionCode(null),
      }}
    >
      {children}
    </SectionErrorContext.Provider>
  );
}

export function useSectionError() {
  const ctx = useContext(SectionErrorContext);
  if (!ctx)
    throw new Error(
      'useSectionError must be used within a SectionErrorProvider'
    );
  return ctx;
}

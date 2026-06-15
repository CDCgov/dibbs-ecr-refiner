import { createContext, useContext, useState } from 'react';

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

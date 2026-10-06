import { ModalProvider } from '@components/Modal/ModalProvider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ReactNode } from 'react';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        enabled: false,
      },
    },
  });

export function TestProviders({ children }: { children: ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ModalProvider>{children}</ModalProvider>
    </QueryClientProvider>
  );
}

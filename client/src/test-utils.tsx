import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ReactNode } from 'react';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

export const TestQueryClientProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

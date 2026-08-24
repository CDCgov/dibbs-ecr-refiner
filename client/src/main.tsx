import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App.tsx';
import { BrowserRouter } from 'react-router';
import '@fontsource-variable/merriweather';
import '@fontsource-variable/public-sans';
import '@trussworks/react-uswds/lib/index.css';
import './tailwind.css';
import './styles/index.scss';
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import { isAxiosError } from 'axios';

function handleSessionExpiry(error: Error) {
  if (isAxiosError(error) && error.response?.status === 401) {
    window.location.href = '/expired';
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 0,
      retry: 2,
    },
    mutations: {
      gcTime: 0,
    },
  },
  queryCache: new QueryCache({
    onError: handleSessionExpiry,
  }),
  mutationCache: new MutationCache({
    onError: handleSessionExpiry,
  }),
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
);

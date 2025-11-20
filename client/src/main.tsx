import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App.tsx';
import { BrowserRouter } from 'react-router';
import '@fontsource-variable/merriweather';
import '@fontsource-variable/public-sans';
import '@trussworks/react-uswds/lib/index.css';
import './tailwind.css';
import './styles/index.scss';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
);

import { render, screen } from '@testing-library/react';

import App from './App';
import { BrowserRouter } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();
const renderApp = () => {
  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe('App', () => {
  it('App renders expected text', () => {
    renderApp();
    expect(screen.getByText('Focus on what matters.')).toBeInTheDocument();
  });
});

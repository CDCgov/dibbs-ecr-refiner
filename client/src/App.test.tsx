import { render, screen } from '@testing-library/react';
import App from './App';
import { BrowserRouter } from 'react-router';
import { TestQueryClientProvider } from './test-utils';

// Set up a mock user
vi.mock('./hooks/Login', async () => {
  const actual = await vi.importActual('./hooks/Login');
  return {
    ...actual,
    useLogin: vi.fn(() => [
      { id: '1', username: 'test', email: 'test@example.com' },
      false,
    ]),
  };
});

// Mock configurations request
vi.mock('./api/configurations/configurations', async () => {
  const actual = await vi.importActual('./api/configurations/configurations');
  return {
    ...actual,
    useGetConfigurations: vi.fn(() => ({
      data: { data: [{ id: '1', display_name: 'test' }] },
      isLoading: false,
      error: null,
    })),
  };
});

const renderApp = () => {
  return render(
    <TestQueryClientProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </TestQueryClientProvider>
  );
};

describe('App', () => {
  it('App renders expected text', async () => {
    renderApp();
    expect(
      await screen.findByText('Your reportable condition configurations')
    ).toBeInTheDocument();
  });
});

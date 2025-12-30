import { render, screen } from '@testing-library/react';
import { App } from './App';
import { BrowserRouter } from 'react-router';
import { TestQueryClientProvider } from './test-utils';

// Set up a mock user
vi.mock('./hooks/Login', async () => {
  const actual = await vi.importActual('./hooks/Login');
  return {
    ...actual,
    useLogin: vi.fn(() => [
      { id: '1', username: 'test', jurisdiction_id: 'jd' },
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
    <BrowserRouter>
      <TestQueryClientProvider>
        <App />
      </TestQueryClientProvider>
    </BrowserRouter>
  );
};

describe('App', () => {
  it('Should render expected text', async () => {
    renderApp();

    expect(
      await screen.findByText('Your reportable condition configurations')
    ).toBeInTheDocument();
  });

  it('Should display a deployed version code to the user', () => {
    vi.stubEnv('VITE_GIT_HASH', 'test-hash');

    renderApp();

    expect(screen.getByText(`Version code: test-hash`)).toBeInTheDocument();
  });

  it('Should show the username and their jurisdiction in the header', async () => {
    renderApp();

    expect(await screen.findByText('test (jd)')).toBeInTheDocument();
  });
});

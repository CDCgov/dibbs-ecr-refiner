import { render, screen } from '@testing-library/react';
import { App } from './App';
import { MemoryRouter } from 'react-router';
import { TestQueryClientProvider } from './test-utils';

vi.mock('./api/user/user', () => ({
  useGetUser: vi.fn(() => ({
    data: null,
    isPending: false,
  })),
}));

// Set up a mock user
vi.mock('./hooks/useLogin', () => ({
  useLogin: vi.fn(() => ({
    user: {
      id: '1',
      username: 'test',
      jurisdiction_id: 'jd',
      notifications: {
        to_render: {
          most_recent_app_update: false,
        },
      },
    },
    isLoading: false,
    refreshUser: vi.fn(),
  })),
}));

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
    <MemoryRouter initialEntries={['/']}>
      <TestQueryClientProvider>
        <App />
      </TestQueryClientProvider>
    </MemoryRouter>
  );
};

describe('App', () => {
  it('Should render expected text', () => {
    renderApp();
    expect(
      screen.getByRole('heading', { name: 'Configurations' })
    ).toBeInTheDocument();
  });

  it('Should display a deployed version code to the user', () => {
    vi.stubEnv('VITE_GIT_HASH', 'a1b2c3d4e5f67890abcdef1234567890abcdef12');

    renderApp();

    expect(screen.getByText('Version code: a1b2c3d')).toBeInTheDocument();
  });

  it('Should show the username and their jurisdiction in the header', async () => {
    renderApp();

    expect(await screen.findByText('test (jd)')).toBeInTheDocument();
  });
});

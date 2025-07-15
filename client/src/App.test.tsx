import { render, screen } from '@testing-library/react';
import App from './App';
import { BrowserRouter } from 'react-router';

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

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('App', () => {
  it('App renders expected text', () => {
    renderApp();
    expect(
      screen.getByText('Your reportable condition configurations')
    ).toBeInTheDocument();
  });
});

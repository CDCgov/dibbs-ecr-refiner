import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';
import { TestQueryClientProvider } from '../../../test-utils';

describe('Config activation page', () => {
  function renderPage() {
    return render(
      <TestQueryClientProvider>
        <MemoryRouter initialEntries={['/configurations/config-id/activate']}>
          <Routes>
            <Route
              path="/configurations/:id/activate"
              element={<ConfigActivate />}
            />
          </Routes>
        </MemoryRouter>
      </TestQueryClientProvider>
    );
  }

  it('should show "Activate" as the current step', () => {
    renderPage();
    expect(screen.getByText('Build', { selector: 'a' })).toBeInTheDocument();
    expect(screen.getByText('Test', { selector: 'a' })).toBeInTheDocument();

    // TODO: Uncomment this when we want to show the Activate screen again
    // expect(screen.getByText('Activate', { selector: 'a' })).toHaveAttribute(
    //   'aria-current',
    //   'page'
    // );
  });
});

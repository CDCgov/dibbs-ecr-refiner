import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';

describe('Config activation page', () => {
  function renderPage() {
    return render(
      <MemoryRouter initialEntries={['/configurations/config-id/activate']}>
        <Routes>
          <Route
            path="/configurations/:id/activate"
            element={<ConfigActivate />}
          />
        </Routes>
      </MemoryRouter>
    );
  }

  it('should show "Activate" as the current step', () => {
    renderPage();
    expect(screen.getByText('Build', { selector: 'a' })).toBeInTheDocument();
    expect(screen.getByText('Test', { selector: 'a' })).toBeInTheDocument();
    expect(screen.getByText('Activate', { selector: 'a' })).toHaveAttribute(
      'aria-current',
      'page'
    );
  });
});

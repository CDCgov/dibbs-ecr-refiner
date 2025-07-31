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

  it('should show "Turn on configuration" as the current step', () => {
    renderPage();
    expect(
      screen.getByText('Build configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Test configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Turn on configuration', { selector: 'a' })
    ).toHaveAttribute('aria-current', 'page');
  });
});

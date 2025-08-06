import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';

describe('Config testing page', () => {
  function renderPage() {
    return render(
      <MemoryRouter initialEntries={['/configurations/config-id/test']}>
        <Routes>
          <Route path="/configurations/:id/test" element={<ConfigActivate />} />
        </Routes>
      </MemoryRouter>
    );
  }

  it('should show "Test configuration" as the current step', () => {
    renderPage();
    expect(
      screen.getByText('Build configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Test configuration', { selector: 'a' })
    ).toHaveAttribute('aria-current', 'page');
    expect(
      screen.getByText('Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();
  });
});

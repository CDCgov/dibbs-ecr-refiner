import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';
import userEvent from '@testing-library/user-event';

describe('Config builder page', () => {
  function renderPage() {
    return render(
      <MemoryRouter initialEntries={['/configurations/config-id/build']}>
        <Routes>
          <Route
            path="/configurations/:id/build"
            element={<ConfigActivate />}
          />
        </Routes>
      </MemoryRouter>
    );
  }

  it('should show "Build configuration" as the current step', () => {
    renderPage();
    expect(
      screen.getByText('Build configuration', { selector: 'a' })
    ).toHaveAttribute('aria-current', 'page');
    expect(
      screen.getByText('Test configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();
  });

  it('should render code set buttons', () => {
    renderPage();
    expect(
      screen.getByText('COVID-19', { selector: 'span' })
    ).toBeInTheDocument();
    expect(screen.getByText('Chlamydia')).toBeInTheDocument();
    expect(
      screen.getByText('Gonorrhea', { selector: 'span' })
    ).toBeInTheDocument();
  });

  it('should show table rows after selecting a code set', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('COVID-19', { selector: 'span' }));

    // Table displays upon code set button click
    expect(screen.getByRole('table')).toBeInTheDocument();

    // 1 header + 9 codes
    expect(screen.getAllByRole('row')).toHaveLength(1 + 9);
  });

  it('should filter codes by code system', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('COVID-19', { selector: 'span' }));

    const select = screen.getByLabelText(/code system/i);
    await user.selectOptions(select, 'SNOMED');

    // Should be only SNOMED codes
    expect(
      screen
        .getAllByRole('row')
        .slice(1)
        .every((row) => within(row).getByText(/SNOMED/))
    ).toBe(true);
  });

  it('should filter codes by search text', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('COVID-19', { selector: 'span' }));

    const searchBox = screen.getByPlaceholderText(/search code set/i);
    await user.type(searchBox, '45068-1');
    expect(searchBox).toHaveValue('45068-1');

    // This will match all rows since the test data is very similar
    // However, 45068-1 will match perfectly and should get pushed to the first row
    const rows = screen.getAllByRole('row').slice(1);
    expect(rows).toHaveLength(9);
    expect(within(rows[0]).getByText('45068-1')).toBeInTheDocument();
  });
});

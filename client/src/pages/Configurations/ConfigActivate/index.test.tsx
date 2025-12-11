import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { ConfigActivate } from '.';
import { TestQueryClientProvider } from '../../../test-utils';
import { DbTotalConditionCodeCount } from '../../../api/schemas';

// Mock all API requests.
const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
];

// Mock configurations request
vi.mock('../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          display_name: 'COVID-19',
          code_sets: mockCodeSets,
          custom_codes: [],
          included_conditions: [
            { id: 'covid-1', display_name: 'COVID-19', associated: true },
          ],
          all_versions: [{ version: 1 }],
        },
      },
    })),
  };
});

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
    expect(screen.getByText('Activate', { selector: 'a' })).toHaveAttribute(
      'aria-current',
      'page'
    );
  });
});

import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  DbConfigurationCustomCode,
  DbTotalConditionCodeCount,
} from '../../../api/schemas';

// Mock all API requests.
const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
  { condition_id: 'chlamydia-1', display_name: 'Chlamydia', total_codes: 8 },
  { condition_id: 'gonorrhea-1', display_name: 'Gonorrhea', total_codes: 5 },
];

const mockCustomCodes: DbConfigurationCustomCode[] = [
  { code: 'custom-code1', name: 'test-custom-code1', system: 'ICD-10' },
];

// Mock configurations request
vi.mock('../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useAddCustomCodeToConfiguration: vi.fn(),
    useDeleteCustomCodeFromConfiguration: vi.fn(),
    useEditCustomCodeFromConfiguration: vi.fn(),
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          display_name: 'COVID-19',
          code_sets: mockCodeSets,
          custom_codes: mockCustomCodes,
          included_conditions: [
            { id: 'covid-1', display_name: 'COVID-19', associated: true },
            { id: 'chlamydia-1', display_name: 'Chlamydia', associated: false },
            { id: 'gonorrhea-1', display_name: 'Gonorrhea', associated: false },
          ],
        },
      },
      isLoading: false,
      isError: false,
    })),
  };
});

describe('Config testing page', () => {
  function renderPage() {
    return render(
      <TestQueryClientProvider>
        <MemoryRouter initialEntries={['/configurations/config-id/test']}>
          <Routes>
            <Route
              path="/configurations/:id/test"
              element={<ConfigActivate />}
            />
          </Routes>
        </MemoryRouter>
      </TestQueryClientProvider>
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

import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigBuild from '.';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  DbConfigurationCustomCode,
  DbTotalConditionCodeCount,
} from '../../../api/schemas';

const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
  { condition_id: 'chlamydia-1', display_name: 'Chlamydia', total_codes: 8 },
  { condition_id: 'gonorrhea-1', display_name: 'Gonorrhea', total_codes: 5 },
];

const mockCustomCodes: DbConfigurationCustomCode[] = [
  { code: 'custom-code1', name: 'test-custom-code1', system: 'ICD-10' },
  { code: 'custom-code2', name: 'test-custom-code2', system: 'RxNorm' },
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
          custom_codes: mockCustomCodes,
        },
      },
      isLoading: false,
      isError: false,
    })),
  };
});

vi.mock('../../../api/conditions/conditions', async () => {
  const actual = await vi.importActual('../../../api/conditions/conditions');
  return {
    ...actual,
    useGetCondition: vi.fn(() => ({
      data: {
        data: {
          id: 'covid-1',
          display_name: 'COVID-19',
          available_systems: ['LOINC', 'SNOMED'],
          codes: [
            { code: '1', system: 'LOINC', description: 'idk' },
            { code: '2', system: 'SNOMED', description: 'example' },
          ],
        },
      },
      isLoading: false,
      isError: false,
    })),
  };
});

describe('Config builder page', () => {
  function renderPage() {
    return render(
      <TestQueryClientProvider>
        <MemoryRouter initialEntries={['/configurations/config-id/build']}>
          <Routes>
            <Route path="/configurations/:id/build" element={<ConfigBuild />} />
          </Routes>
        </MemoryRouter>
      </TestQueryClientProvider>
    );
  }

  it('should show "Build configuration" as the current step', async () => {
    renderPage();
    expect(
      await screen.findByText('Build configuration', { selector: 'a' })
    ).toHaveAttribute('aria-current', 'page');
    expect(
      await screen.findByText('Test configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      await screen.findByText('Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();
  });

  it('should render code set buttons', async () => {
    renderPage();
    expect(
      await screen.findByText('COVID-19', { selector: 'span' })
    ).toBeInTheDocument();
    expect(
      await screen.findByText('Chlamydia', { selector: 'span' })
    ).toBeInTheDocument();
    expect(
      await screen.findByText('Gonorrhea', { selector: 'span' })
    ).toBeInTheDocument();
  });

  it('should show table rows after selecting a code set', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText('COVID-19', { selector: 'span' }));

    // Table displays upon code set button click
    expect(screen.getByRole('table')).toBeInTheDocument();

    expect(await screen.findAllByRole('row')).toHaveLength(mockCodeSets.length);
  });

  it('should filter codes by code system', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByText('COVID-19', { selector: 'span' }));

    const parentContainer = await screen.findByTestId(
      'code-system-select-container'
    ); // name of the `data-testid` added to the parent div
    const select = within(parentContainer).getByLabelText(/code system/i);
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
    const covidCode = '1';
    renderPage();

    await user.click(await screen.findByText('COVID-19', { selector: 'span' }));

    const searchBox = await screen.findByPlaceholderText(/search/i);
    await user.type(searchBox, covidCode);
    expect(searchBox).toHaveValue(covidCode);

    // wait for debounced search results to appear before checking
    await waitFor(async () => {
      const rows = (await screen.findAllByRole('row')).slice(1);
      expect(rows).toHaveLength(1);
    });

    const row = await screen.findByText(covidCode);
    expect(row).toBeInTheDocument();
  });
});

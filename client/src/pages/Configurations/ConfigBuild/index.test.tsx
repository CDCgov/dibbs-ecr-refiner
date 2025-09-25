import { render, screen, waitFor, within } from '@testing-library/react';

import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigBuild from '.';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  DbConfigurationCustomCode,
  DbTotalConditionCodeCount,
} from '../../../api/schemas';
import {
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useDeleteCustomCodeFromConfiguration,
} from '../../../api/configurations/configurations';
import { Mock } from 'vitest';

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
    useGetConditions: vi.fn(() => ({
      data: {
        data: [
          { id: 'covid-1', display_name: 'COVID-19' },
          { id: 'chlamydia-1', display_name: 'Chlamydia' },
          { id: 'gonorrhea-1', display_name: 'Gonorrhea' },
        ],
      },
      isLoading: false,
      error: null,
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

    const searchBox = await screen.findByPlaceholderText(/Search code set/);
    await user.type(searchBox, covidCode);
    expect(searchBox).toHaveValue(covidCode);

    // wait for debounced search results to appear before checking
    await waitFor(async () => {
      const rows = (await screen.findAllByRole('row')).slice(1);
      expect(rows).toHaveLength(1);
    });

    const row = await screen.findByText(covidCode, { selector: 'mark' });
    expect(row).toBeInTheDocument();
  });

  it('should add a custom code', async () => {
    const user = userEvent.setup();
    renderPage();

    (useAddCustomCodeToConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    await user.click(screen.getByText('Custom codes', { selector: 'span' }));
    expect(
      screen.getByText(
        'Add codes that are not included in the code sets from the'
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText('Add code', { selector: 'button' })
    ).toBeInTheDocument();

    await user.click(screen.getByText('Add code', { selector: 'button' }));
    expect(
      screen.getByText('Add custom code', { selector: 'h2' })
    ).toBeInTheDocument();

    expect(
      screen.getByText('Add custom code', { selector: 'button' })
    ).toBeDisabled();
    await user.type(screen.getByLabelText('Code #'), '12345');
    await user.selectOptions(screen.getByLabelText('Code system'), 'SNOMED');
    await user.type(screen.getByLabelText('Code name'), 'Test code name');

    expect(
      screen.getByText('Add custom code', { selector: 'button' })
    ).not.toBeDisabled();
    await user.click(
      screen.getByText('Add custom code', { selector: 'button' })
    );
  });

  it('should edit an existing custom code', async () => {
    const user = userEvent.setup();
    renderPage();

    (useAddCustomCodeToConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    await user.click(screen.getByText('Custom codes', { selector: 'span' }));
    expect(
      screen.getByText(
        'Add codes that are not included in the code sets from the'
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText('Edit', { selector: 'button' })
    ).toBeInTheDocument();

    await user.click(screen.getByText('Edit', { selector: 'button' }));
    expect(
      screen.getByText('Edit custom code', { selector: 'h2' })
    ).toBeInTheDocument();

    expect(screen.getByText('Update', { selector: 'button' })).toBeEnabled();
    expect(screen.getByLabelText('Code #')).toHaveValue('custom-code1');
    expect(screen.getByLabelText('Code system')).toHaveValue('icd-10');
    expect(screen.getByLabelText('Code name')).toHaveValue('test-custom-code1');

    await user.type(screen.getByLabelText('Code #'), '12345');

    expect(
      screen.getByText('Update', { selector: 'button' })
    ).not.toBeDisabled();
    await user.click(screen.getByText('Update', { selector: 'button' }));
  });

  it('should delete an existing custom code', async () => {
    const user = userEvent.setup();
    renderPage();

    (useAddCustomCodeToConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    await user.click(screen.getByText('Custom codes', { selector: 'span' }));
    expect(
      screen.getByText(
        'Add codes that are not included in the code sets from the'
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText('Delete', { selector: 'button' })
    ).toBeInTheDocument();

    await user.click(screen.getByText('Delete', { selector: 'button' }));
  });

  it('should display an "Export configuration" button', () => {
    renderPage();
    expect(
      screen.getByText('Export configuration', { selector: 'a' })
    ).toBeInTheDocument();
  });
});

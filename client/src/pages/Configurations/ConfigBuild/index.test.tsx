import { render, screen, waitFor, within } from '@testing-library/react';

import { MemoryRouter, Route, Routes } from 'react-router';
import { ConfigBuild } from '.';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  DbConfigurationCustomCode,
  DbTotalConditionCodeCount,
  GetConfigurationResponse,
  GetConfigurationResponseVersion,
} from '../../../api/schemas';
import {
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useDeleteCustomCodeFromConfiguration,
  useGetConfiguration,
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

const mockVersions: GetConfigurationResponseVersion[] = [
  {
    id: 'config-id',
    version: 2,
    status: 'draft',
    condition_canonical_url:
      'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
  },
  {
    id: 'prev-id',
    version: 1,
    status: 'inactive',
    condition_canonical_url:
      'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
  },
];

const baseMockConfig: GetConfigurationResponse = {
  id: 'config-id',
  condition_id: 'covid-19',
  draft_id: 'config-id',
  is_draft: true,
  display_name: 'COVID-19',
  status: 'draft',
  code_sets: mockCodeSets,
  custom_codes: mockCustomCodes,
  section_processing: [],
  included_conditions: [],
  deduplicated_codes: ['123456'],
  all_versions: mockVersions,
  version: 2,
  active_version: null,
  latest_version: 2,
  canonical_url: 'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
};

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
        data: baseMockConfig,
      },
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
    })),
    useGetConditions: vi.fn(() => ({
      data: {
        data: [
          { id: 'covid-1', display_name: 'COVID-19' },
          { id: 'chlamydia-1', display_name: 'Chlamydia' },
          { id: 'gonorrhea-1', display_name: 'Gonorrhea' },
        ],
      },
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
    expect(await screen.findByText('Build', { selector: 'a' })).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(
      await screen.findByText('Test', { selector: 'a' })
    ).toBeInTheDocument();
    // TODO: Uncomment this when we want to show the Activate screen again
    // expect(
    //   await screen.findByText('Activate', { selector: 'a' })
    // ).toBeInTheDocument();
  });

  it('should render a version menu with previous versions', async () => {
    const expectedMenuText = 'Editing: Version 2';
    const user = userEvent.setup();
    renderPage();
    expect(await screen.findByText(expectedMenuText)).toBeInTheDocument();
    await user.click(await screen.findByText(expectedMenuText));
    expect(await screen.findAllByRole('menuitem')).toHaveLength(2);
  });

  it("should render the configuration's inactive status", async () => {
    renderPage();
    expect(await screen.findByText('Status: Inactive')).toBeInTheDocument();
  });

  it("should render the configuration's active status", async () => {
    (useGetConfiguration as unknown as Mock).mockReturnValue({
      data: {
        data: {
          ...baseMockConfig,
          status: 'active',
          active_version: 1,
          version: 1,
        },
      },
    });
    renderPage();
    expect(
      await screen.findByText('Status: Version 1 active')
    ).toBeInTheDocument();
  });

  it('should render banner to make a new draft configuration', async () => {
    (useGetConfiguration as unknown as Mock).mockReturnValue({
      data: {
        data: {
          ...baseMockConfig,
          status: 'active',
          active_version: 1,
          version: 1,
          is_draft: false,
          draft_id: null,
        },
      },
    });
    renderPage();
    expect(
      await screen.findByText(/You must draft a new version to make changes/i)
    ).toBeInTheDocument();
    expect(
      await screen.findByRole('button', { name: 'Draft a new version' })
    ).toBeInTheDocument();
  });

  it('should render banner to go to existing draft configuration', async () => {
    (useGetConfiguration as unknown as Mock).mockReturnValue({
      data: {
        data: {
          ...baseMockConfig,
          status: 'active',
          active_version: 1,
          version: 1,
          is_draft: false,
          draft_id: 'test-id',
        },
      },
    });
    renderPage();
    expect(
      await screen.findByText(/You can edit the existing draft/i)
    ).toBeInTheDocument();
    expect(
      await screen.findByRole('link', { name: 'Go to draft' })
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

  it('should throw an error when adding an existing custom code', async () => {
    const user = userEvent.setup();
    renderPage();

    (useAddCustomCodeToConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
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
    await user.type(screen.getByLabelText('Code #'), '123456');
    await userEvent.tab(); // triggers onBlur

    expect(
      await screen.findByText(
        'The code "123456" already exists in the condition code set.',
        { selector: 'p' }
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText('Add custom code', { selector: 'button' })
    ).toBeDisabled();
  });

  it('should add a custom code', async () => {
    const user = userEvent.setup();
    renderPage();

    (useAddCustomCodeToConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
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
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
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
      reset: vi.fn(),
    });

    (useEditCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
      reset: vi.fn(),
    });

    (useDeleteCustomCodeFromConfiguration as unknown as Mock).mockReturnValue({
      mutate: vi.fn().mockReturnValue({ data: {} }),
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

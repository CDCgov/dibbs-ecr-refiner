import { describe, it, expect, vi, Mock } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { ConfigBuild } from '.';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useDeleteCustomCodeFromConfiguration,
  useGetConfiguration,
  useUploadCustomCodesCsv,
  useValidateCustomCodeFromConfiguration,
} from '../../../api/configurations/configurations';
import {
  baseMockConfig,
  MOCK_CONFIG_DRAFT_ID,
  MOCK_CONFIG_ID,
  mockCodeSets,
  mockCodeSystems,
} from '../../../utils/fixtures';

vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({
    count,
    estimateSize,
  }: {
    count: number;
    estimateSize: () => number;
  }) => ({
    getVirtualItems: () =>
      Array.from({ length: count }, (_, i) => ({
        index: i,
        start: i * estimateSize(),
        end: (i + 1) * estimateSize(),
        size: estimateSize(),
        key: i,
        lane: 0,
      })),
    getTotalSize: () => count * estimateSize(),
  }),
}));

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
    useUploadCustomCodesCsv: vi.fn(),
    useValidateCustomCodeFromConfiguration: vi.fn(),
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
          completeness_status: {
            code_set_status: 'fully complete',
            code_category_statuses: [],
          },
          codes: [
            { code: '1', system: 'LOINC', description: 'idk' },
            { code: '2', system: 'SNOMED', description: 'example' },
          ],

          systems: mockCodeSystems,
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

vi.mock('../../../api/code-systems/code-systems', () => {
  return {
    useGetCodeSystems: vi.fn(() => ({
      data: {
        data: mockCodeSystems,
      },
    })),
  };
});

describe('Config builder page', () => {
  it('shows lock banner and disables edit controls when locked by another user', async () => {
    const user = userEvent.setup();
    (useGetConfiguration as unknown as Mock).mockReturnValue({
      data: {
        data: {
          ...baseMockConfig,
          is_locked: true,
          locked_by: {
            id: 'other-user-id',
            name: 'Jane Doe',
            email: 'jane@foo.com',
          },
        },
      },
    });

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
    render(
      <MemoryRouter initialEntries={['/configurations/config-id/build']}>
        <TestQueryClientProvider>
          <Routes>
            <Route path="/configurations/:id/build" element={<ConfigBuild />} />
          </Routes>
        </TestQueryClientProvider>
      </MemoryRouter>
    );
    const lockBanner = await screen.findByRole('status');
    expect(within(lockBanner).getByText(/View only:/i)).toBeInTheDocument();
    expect(screen.getByText(/Jane Doe/)).toBeInTheDocument();
    // The ADD button shouldn't be in the document
    expect(
      screen.queryByRole('button', { name: /add new code set/i })
    ).not.toBeInTheDocument();
    // The custom code add button should be disabled
    // Switch to the custom codes tab to render the button
    const customCodesTab = await screen.findByRole('button', {
      name: /custom codes/i,
    });
    await user.click(customCodesTab);
    // Assert the "Custom codes" heading is present
    expect(
      await screen.findByRole('heading', { name: /custom codes/i })
    ).toBeInTheDocument();

    const addCustomCodeBtn = await screen.findByRole('button', {
      name: /add new custom code/i,
    });
    expect(addCustomCodeBtn).toBeDisabled();
  });
  function renderPage() {
    return render(
      <MemoryRouter
        initialEntries={[`/configurations/${MOCK_CONFIG_ID}/build`]}
      >
        <TestQueryClientProvider>
          <Routes>
            <Route path="/configurations/:id/build" element={<ConfigBuild />} />
          </Routes>
        </TestQueryClientProvider>
      </MemoryRouter>
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
    expect(
      await screen.findByText('Activate', { selector: 'a' })
    ).toBeInTheDocument();
  });

  it('should render a version menu with previous versions', async () => {
    const user = userEvent.setup();
    const expectedMenuText = 'Editing: Version 2';
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
    const user = userEvent.setup();
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

    // editing should be disabled
    await user.click(screen.getByText('Custom codes'));
    expect(
      await screen.findByRole('button', { name: 'Add new custom code' })
    ).toBeDisabled();

    await user.click(screen.getByText('Sections'));
    expect(screen.getByRole('checkbox')).toHaveAttribute('data-disabled'); // headless UI's checkbox uses this attribute to say its disabled
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
          draft_id: MOCK_CONFIG_DRAFT_ID,
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

  it('should display user and status information in the version picker menu', async () => {
    const expectedMenuText = 'Editing: Version 2';
    const user = userEvent.setup();
    (useGetConfiguration as unknown as Mock).mockReturnValue({
      data: {
        data: {
          ...baseMockConfig,
          status: 'draft',
          active_version: 1,
          version: 2,
          is_draft: true,
          draft_id: MOCK_CONFIG_DRAFT_ID,
        },
      },
    });
    renderPage();

    // check that menu structure looks accurate
    expect(await screen.findByText(expectedMenuText)).toBeInTheDocument();
    await user.click(await screen.findByText(expectedMenuText));
    const menuItems = await screen.findAllByRole('menuitem');
    expect(menuItems).toHaveLength(2);

    // check that draft config displays info in the expected format
    const draft = menuItems[0];
    const expectedDraftTextFormat =
      /^Version 2 Draft created (\d{2}\/\d{2}\/\d{4}), (\d{1,2}:\d{2} (AM|PM)) by mock-user-1$/;
    expect(draft).toHaveTextContent(expectedDraftTextFormat);

    // check that active config displays info in the expected format
    const active = menuItems[1];
    const expectedActiveTextFormat =
      /^Version 1 \(Active\)Last activated (\d{2}\/\d{2}\/\d{4}), (\d{1,2}:\d{2} (AM|PM)) by mock-user-2$/;
    expect(active).toHaveTextContent(expectedActiveTextFormat);
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

    const select = screen.getByLabelText(/code system/i);

    // expect the list of code system options to match the list of expected values
    const optionList = within(select)
      .getAllByRole('option')
      .map((o) => o.textContent);
    mockCodeSystems.forEach((c) => {
      expect(optionList.includes(c.key));
    });
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
    (useValidateCustomCodeFromConfiguration as unknown as Mock).mockReturnValue(
      {
        mutate: vi.fn().mockImplementation((_vars, { onSuccess }) => {
          onSuccess({ data: { valid: false } });
        }),
      }
    );

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

    const user = userEvent.setup();
    renderPage();

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
    await user.type(screen.getByLabelText('Code'), '123456');
    await user.tab(); // triggers onBlur

    expect(
      await screen.findByText('The code "123456" already exists.', {
        selector: 'p',
      })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Add custom code', { selector: 'button' })
    ).toBeDisabled();
  });

  it('should add a custom code', async () => {
    (useValidateCustomCodeFromConfiguration as unknown as Mock).mockReturnValue(
      {
        mutate: vi.fn().mockImplementation((_vars, { onSuccess }) => {
          onSuccess({ data: { valid: true } });
        }),
      }
    );

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
    const user = userEvent.setup();
    renderPage();

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

    await user.type(screen.getByLabelText('Code'), '12345');
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

    (useValidateCustomCodeFromConfiguration as unknown as Mock).mockReturnValue(
      {
        mutate: vi.fn().mockReturnValue(true),
        reset: vi.fn(),
      }
    );

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
    expect(screen.getByLabelText('Code')).toHaveValue('custom-code1');
    expect(screen.getByLabelText('Code name')).toHaveValue('test-custom-code1');
    expect(screen.getByLabelText('Code system')).toHaveValue('icd10');

    await user.type(screen.getByLabelText('Code'), '12345');

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

  it('should bulk upload custom codes from a CSV file', async () => {
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

    const uploadMutate = vi.fn((_vars, opts) => {
      opts?.onSuccess?.({
        data: {
          message: 'Successfully uploaded custom codes.',
          codes_processed: 2,
          total_custom_codes_in_configuration: 2,
          preview_items: [],
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {},
      });

      opts?.onSettled?.();
    });

    (useUploadCustomCodesCsv as unknown as Mock).mockReturnValue({
      mutate: uploadMutate,
      reset: vi.fn(),
      isPending: false,
    });

    await user.click(screen.getByText('Custom codes', { selector: 'span' }));

    await user.click(
      screen.getByText('Import from CSV', { selector: 'button' })
    );

    expect(
      screen.getByText('Import from CSV', { selector: 'h2' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Upload CSV', { selector: 'button' })
    ).toBeInTheDocument();

    const csv = `code,code_system,display_name
12345,LOINC,TEST 1
6789,LOINC,TEST 2
`;
    const file = new File([csv], 'custom_codes.csv', { type: 'text/csv' });

    const input = document.querySelector(
      'input[type="file"]'
    ) as HTMLInputElement;

    await user.upload(input, file);

    expect(uploadMutate).toHaveBeenCalledTimes(1);

    const call = uploadMutate.mock.calls[0];
    const vars = call[0];

    expect(vars).toMatchObject({
      configurationId: expect.anything(),
      data: {
        csv_text: expect.any(String),
        filename: 'custom_codes.csv',
      },
    });

    expect(vars.data.csv_text).toContain('code,code_system,display_name');
    expect(vars.data.csv_text).toContain('12345,LOINC,TEST 1');

    // was: assert <h3>Custom codes</h3>
    // UI shows "Import from CSV" h2 after upload, not always custom tab
    expect(
      screen.getByText('Import from CSV', { selector: 'h2' })
    ).toBeInTheDocument();
  });

  it('downloads the custom code upload template CSV', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByText('Custom codes', { selector: 'span' }));

    await user.click(
      screen.getByText('Import from CSV', { selector: 'button' })
    );

    expect(
      await screen.findByRole('heading', { name: /import from csv/i })
    ).toBeInTheDocument();

    const createObjectUrlSpy = vi
      .spyOn(URL, 'createObjectURL')
      .mockReturnValue('blob:mock-url');

    const revokeObjectUrlSpy = vi
      .spyOn(URL, 'revokeObjectURL')
      .mockImplementation(() => {});

    await user.click(
      await screen.findByRole('button', { name: /download template/i })
    );

    expect(createObjectUrlSpy).toHaveBeenCalledTimes(1);

    const blobArg = createObjectUrlSpy.mock.calls[0][0] as Blob;

    const text = await blobArg.text();
    // one row for each code system systems plus header
    expect(text.trim().split('\n').length).toBe(mockCodeSystems.length + 1);

    // cleanup
    createObjectUrlSpy.mockRestore();
    revokeObjectUrlSpy.mockRestore();
  });
});

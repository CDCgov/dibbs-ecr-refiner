import { describe, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';

import { ManageCodes } from '.';
import { ToastContainer } from 'react-toastify';
import { TestProviders } from '../../../test-utils';
import {
  testCodeCounts,
  testCodeResponse,
  testCustomCodes,
  testFiltersResponse,
  testTesCodes,
} from './fixtures';
import userEvent from '@testing-library/user-event';
import { useFilterState } from './useFilterState';

// Mock all API requests.
vi.mock('../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useGetConfigurations: vi.fn(() => ({
      data: {
        data: [{ id: 'config-id', name: 'Anaplasmosis', is_active: false }],
      },
    })),
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          status: 'draft',
          draft_id: 'config-id',
          display_name: 'Anaplasmosis',
          is_draft: true,
          code_sets: [],
          custom_codes: {
            codes: [],
            code_systems: {},
          },
          rsg_codes: [{ display: 'Anaplasmosis (disorder)', code: '13906002' }],
          included_conditions: [
            { id: '1', display_name: 'Anaplasmosis', associated: true },
            {
              id: 'exists-id',
              display_name: 'already-created',
              associated: false,
            },
          ],
          all_versions: [],
          section_processing: [],
          active_version: null,
          active_configuration_id: null,
          version: 1,
          latest_version: 1,
          locked_by: null,
          is_locked: false,
        },
      },
    })),

    useGetCodesInfinite: vi.fn(() => ({
      data: { pages: [{ data: testCodeResponse }] },
      isPending: false,
      isError: false,
      fetchNextPage: vi.fn(),
      hasNextPage: true,
      isFetchingNextPage: false,
    })),

    useGetCodeCounts: vi.fn(() => ({
      data: { data: testCodeCounts },
    })),
  };
});

vi.mock('./useFilterState', () => {
  return {
    useFilterState: vi.fn(() => ({
      filters: testFiltersResponse,
    })),
  };
});

vi.mock('../../../api/conditions/conditions', async () => {
  const actual = await vi.importActual('../../../api/conditions/conditions');
  return {
    ...actual,
    useGetConditions: vi.fn(() => ({
      data: {
        data: [
          {
            id: '1',
            display_name: 'Anaplasmosis',
            rsg_codes: [
              { display: 'Anaplasmosis (disorder)', code: '13906002' },
            ],
          },
        ],
      },
    })),
  };
});

const renderPageView = () =>
  render(
    <MemoryRouter initialEntries={['/configurations/config-id/manage-codes']}>
      <TestProviders>
        <ToastContainer />
        <Routes>
          <Route
            path="/configurations/:id/manage-codes"
            element={<ManageCodes />}
          />
        </Routes>
      </TestProviders>
    </MemoryRouter>
  );

describe('Mangage codes page', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders page in MemoryRouter with the correct tab selected', () => {
    renderPageView();
    expect(screen.getByText('Manage codes', { selector: 'a' })).toHaveAttribute(
      'aria-current',
      'page'
    );
  });

  it('should render with expected codesets', () => {
    renderPageView();
    expect(screen.getByText('13906002')).toBeInTheDocument();
    expect(screen.getByText('1111111-cvx')).toBeInTheDocument();
    expect(
      screen.queryByText(
        'Previous versions cannot be modified. You can edit the existing draft.'
      )
    ).not.toBeInTheDocument();
  });

  it('selection and deletion of custom codes should render as expected', async () => {
    const user = userEvent.setup();
    renderPageView();

    for (const c of testCustomCodes) {
      const customCodeCheckbox = screen.getByLabelText(
        `Include ${c.code} in bulk operation`
      );

      await user.click(customCodeCheckbox);
      expect(customCodeCheckbox).toBeChecked();
    }

    expect(screen.getByTestId(`control-panel`)).toBeVisible();
    expect(
      screen.getByText(`${testCustomCodes.length} selected`)
    ).toBeVisible();

    const deselectCode = testCustomCodes[1];
    const customCodeCheckbox = screen.getByLabelText(
      `Include ${deselectCode.code} in bulk operation`
    );

    await user.click(customCodeCheckbox);
    expect(customCodeCheckbox).not.toBeChecked();

    expect(
      screen.getByText(`${testCustomCodes.length - 1} selected`)
    ).toBeVisible();

    await user.click(screen.getByLabelText('More options'));

    const deletionButton = screen.getByText(
      `Delete ${testCustomCodes.length - 1} custom codes`
    );

    expect(deletionButton).toBeVisible();
    await user.click(deletionButton);

    expect(
      screen.getByText(
        `${testCustomCodes.length - 1} custom codes will be deleted`
      )
    );

    const exclusionButton = screen.getByText('Exclude');
    await user.click(exclusionButton);
    expect(
      screen.getByText('None of the selected codes can be excluded.')
    ).toBeVisible();
    expect(
      screen.getByText(
        `${testCustomCodes.length - 1} custom code(s) can't be excluded.`,
        { exact: false }
      )
    ).toBeVisible();
  });

  it('select all modal edge cases render as elected', async () => {
    const user = userEvent.setup();
    renderPageView();

    const selectAllCheckbox = screen.getByLabelText(
      'Include all codes in bulk operation'
    );

    await user.click(selectAllCheckbox);
    expect(screen.getByTestId(`control-panel`)).toBeVisible();
    await user.click(screen.getByLabelText('More options'));

    expect(
      screen.getByText(`Delete ${testCustomCodes.length} custom codes`)
    ).toBeVisible();

    const exclusionButton = screen.getByText('Exclude');

    const rctcCount = testTesCodes.filter((c) => c.is_trigger_code).length;
    const totalCodeCount = testCodeCounts.total_code_count;
    const excludeableCodeCount =
      totalCodeCount - rctcCount - testCustomCodes.length;

    await user.click(exclusionButton);

    expect(
      screen.getByText(
        `${excludeableCodeCount} of ${totalCodeCount} selected codes will be excluded from this configuration.`
      )
    ).toBeVisible();
    expect(
      screen.getByText(
        `${testCustomCodes.length} custom code(s) can't be excluded.`,
        { exact: false }
      )
    ).toBeVisible();
  });

  it('displays a different tally string for the search field', async () => {
    vi.mocked(useFilterState).mockReturnValue({
      filters: { ...testFiltersResponse, search: 'ana' },
    } as any);

    const user = userEvent.setup();
    renderPageView();

    const search = screen.getByPlaceholderText('Search by keyword');
    await user.type(search, 'ana');

    const selectAllCheckbox = screen.getByLabelText(
      'Include all codes in bulk operation'
    );
    await user.click(selectAllCheckbox);
    expect(screen.getByTestId(`control-panel`)).toBeVisible();
    expect(screen.getByText('100+ codes selected')).toBeVisible();
  });
});

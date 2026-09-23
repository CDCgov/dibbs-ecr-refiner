import { describe, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';

import { ManageCodes } from '.';
import { ToastContainer } from 'react-toastify';
import { TestProviders } from '../../../test-utils';
import userEvent from '@testing-library/user-event';
import { anaplasmosisCodeResponse } from './fixtures';

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
    useCreateConfiguration: vi.fn(() => ({
      mutate: vi.fn().mockResolvedValue({ data: {} }),
      reset: vi.fn(),
    })),
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          display_name: 'Anaplasmosis',
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
        },
      },
    })),

    useGetCodesInfinite: vi.fn(() => ({
      data: { pages: [{ data: anaplasmosisCodeResponse }] },
      isPending: false,
      isError: false,
      fetchNextPage: vi.fn(),
      hasNextPage: true,
      isFetchingNextPage: false,
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

describe('Mange Codes Page', () => {
  describe('Minimal Test Case', () => {
    it('renders Manage Codes subpage in MemoryRouter', async () => {
      renderPageView();
      expect(
        screen.getByText('Manage codes', { selector: 'a' })
      ).toHaveAttribute('aria-current', 'page');
    });
  });
  beforeEach(() => vi.resetAllMocks());

  it('should render with expected codesets', async () => {
    renderPageView();

    expect(screen.getByText('13906002')).toBeInTheDocument();
  });
});

import { describe, expect, Mock } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { Configurations } from '.';
import { TestQueryClientProvider } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from 'react-toastify';
import { useCreateConfiguration } from '../../api/configurations/configurations';
import { CreateConfigurationResponse } from '../../api/schemas';
import ConfigBuild from './ConfigBuild';
import { CONFIGURATION_CONFIRMATION_CTA, CONFIGURATION_CTA } from './utils';

// Mock all API requests.
vi.mock('../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../api/configurations/configurations'
  );
  return {
    ...actual,
    useGetConfigurations: vi.fn(() => ({
      data: {
        data: [
          { id: '1', name: 'COVID-19', is_active: true },
          { id: '2', name: 'Zika Virus Disease', is_active: true },
          { id: '3', name: 'Zika Virus Disease', is_active: false },
        ],
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
          code_sets: [], // not needed for these tests
          custom_codes: [], // not needed for these tests
          included_conditions: [
            { id: '1', display_name: 'Anaplasmosis', associated: true },
            {
              id: 'exists-id',
              display_name: 'already-created',
              associated: false,
            },
          ],
          all_versions: [],
        },
      },
    })),
  };
});

vi.mock('../../api/conditions/conditions', async () => {
  const actual = await vi.importActual('../../api/conditions/conditions');
  return {
    ...actual,
    useGetConditions: vi.fn(() => ({
      data: {
        data: [
          { id: '1', display_name: 'Anaplasmosis' },
          { id: 'exists-id', display_name: 'already-created' },
        ],
      },
    })),
  };
});

const renderPageView = () =>
  render(
    <TestQueryClientProvider>
      <ToastContainer />
      <MemoryRouter initialEntries={['/configurations']}>
        <Routes>
          <Route path="/configurations" element={<Configurations />} />
          <Route path="/configurations/:id/build" element={<ConfigBuild />} />
        </Routes>
      </MemoryRouter>
    </TestQueryClientProvider>
  );

describe('Configurations Page', () => {
  beforeEach(() => vi.resetAllMocks());

  it('should render the Configurations page with title and search bar', async () => {
    renderPageView();
    expect(
      screen.getByText('Your reportable condition configurations')
    ).toBeInTheDocument();
    expect(
      await screen.findByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: CONFIGURATION_CTA })
    ).toBeInTheDocument();
  });

  it('should show an error toast when user attempts to create duplicate config', async () => {
    const user = userEvent.setup();

    // Mock the mutation to trigger onError
    const mockMutate = vi.fn().mockImplementation(
      (
        _: { data: { condition_id: string } },
        options: {
          onSuccess?: (resp: unknown) => void;
          onError?: (e: unknown) => void;
        } = {}
      ) => {
        if (options.onError) {
          options.onError({
            message: 'Configuration could not be created',
          });
        }
      }
    );

    (useCreateConfiguration as unknown as Mock).mockReturnValue({
      mutate: mockMutate,
      reset: vi.fn(),
    });

    renderPageView();

    const setUpButton = screen.getByRole('button', {
      name: CONFIGURATION_CTA,
    });
    await user.click(setUpButton);

    const conditionInput = screen.getByLabelText('Select condition');
    await user.type(conditionInput, 'already-created{enter}');
    expect(conditionInput).toHaveValue('already-created');

    const addConditionButton = screen.getByRole('button', {
      name: CONFIGURATION_CONFIRMATION_CTA,
    });
    await user.click(addConditionButton);

    // Assert that the error toast appears
    expect(
      await screen.findByText('Configuration could not be created')
    ).toBeInTheDocument();
  });

  it('should create a new config and takes the user to the build page', async () => {
    const user = userEvent.setup();

    const response: CreateConfigurationResponse = {
      id: 'config-id',
      name: 'Anaplasmosis',
    };

    const mockMutate = vi.fn().mockImplementation(
      (
        _: { data: { condition_id: string } },
        options: {
          onSuccess?: (resp: unknown) => void;
          onError?: (e: unknown) => void;
        } = {}
      ) => {
        if (options.onSuccess) {
          options.onSuccess({ data: response });
        }
        return Promise.resolve({ data: response });
      }
    );

    // navigate to reportable conditions
    (useCreateConfiguration as unknown as Mock).mockReturnValue({
      mutate: mockMutate,
      data: { data: response },
      reset: vi.fn(),
    });

    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: CONFIGURATION_CTA,
    });
    await user.click(setUpButton);

    const dialog = screen.getByRole('dialog');

    // Check to see if the modal has a class of `is-visible`.
    expect(dialog).toHaveClass('is-visible');

    const conditionInput = screen.getByLabelText('Select condition');
    expect(conditionInput).toBeInTheDocument();

    await user.type(conditionInput, 'Anaplasmosis{enter}');
    expect(conditionInput).toHaveValue('Anaplasmosis');

    // try clearing the input to ensure button gets disabled
    await user.click(screen.getByTestId('combo-box-clear-button'));
    expect(screen.getByLabelText('Select condition')).toHaveValue('');
    expect(
      screen.getByRole('button', {
        name: CONFIGURATION_CONFIRMATION_CTA,
      })
    ).toBeDisabled();

    // re-enter info
    await user.type(conditionInput, 'Anaplasmosis{enter}');
    expect(conditionInput).toHaveValue('Anaplasmosis');

    const addConditionButton = screen.getByRole('button', {
      name: CONFIGURATION_CONFIRMATION_CTA,
    });
    expect(addConditionButton).toBeEnabled();
    await user.click(addConditionButton);

    // Check that navigation to the build page worked
    expect(
      await screen.findByText('Anaplasmosis', { selector: 'h2' })
    ).toBeInTheDocument();

    expect(
      await screen.findByText('New configuration created')
    ).toBeInTheDocument();
  });

  it('should allow users to search for a configuration', async () => {
    const user = userEvent.setup();
    renderPageView();

    // search
    const searchInput = screen.getByPlaceholderText(/search configurations/i);
    await user.type(searchInput, 'cov');
    expect(searchInput).toHaveValue('cov');

    // 2 because header + the row we're looking for
    expect(
      await within(screen.getByRole('table')).findAllByRole('row')
    ).toHaveLength(2);

    // [1] because this is the non-header row we're looking for
    expect(
      (await within(screen.getByRole('table')).findAllByRole('row'))[1]
    ).toHaveTextContent('COVID-19');
  });

  it('should show all configurations if no search text is provided', () => {
    renderPageView();

    const searchInput = screen.getByPlaceholderText(/search configurations/i);
    expect(searchInput).toHaveValue('');

    // 4 because header + all 3 configs
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(
      4
    );
  });
});

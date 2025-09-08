import { describe, expect, Mock } from 'vitest';

// Prevent AggregateError by globally mocking fetch and XMLHttpRequest
beforeAll(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
  );
  global.XMLHttpRequest = vi.fn();
});
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { Configurations } from '.';
import { TestQueryClientProvider } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from 'react-toastify';
import { useCreateConfiguration } from '../../api/configurations/configurations';
import { CreateConfigurationResponse } from '../../api/schemas';
import ConfigBuild from './ConfigBuild';

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
          { id: '1', name: 'test', is_active: true },
          { id: 'exists-id', name: 'already-created', is_active: true },
        ],
      },
      isLoading: false,
      error: null,
    })),
    useCreateConfiguration: vi.fn(() => ({
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    })),
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          display_name: 'Anaplasmosis',
          code_sets: [], // not needed for these tests
          custom_codes: [], // not needed for these tests
        },
      },
      isLoading: false,
      isError: false,
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
      isLoading: false,
      error: null,
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

  test('renders the Configurations page with title and search bar', async () => {
    // Default mock (no need to be called as part of this test)
    (useCreateConfiguration as unknown as Mock).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ data: {} }),
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    renderPageView();
    expect(
      screen.getByText('Your reportable condition configurations')
    ).toBeInTheDocument();
    expect(
      await screen.findByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Set up new condition' })
    ).toBeInTheDocument();
  });

  test('should show an error toast when user attempts to create duplicate config', async () => {
    const user = userEvent.setup();

    // Mock the mutation to trigger onError
    const mockMutateAsync = vi.fn().mockImplementation(
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
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      reset: vi.fn(),
    });

    renderPageView();

    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);

    const conditionInput = screen.getByLabelText('Condition');
    await user.type(conditionInput, 'already-created{enter}');
    expect(conditionInput).toHaveValue('already-created');

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    await user.click(addConditionButton);

    // Assert that the error toast appears
    expect(
      await screen.findByText('Configuration could not be created')
    ).toBeInTheDocument();
  });

  test('should create a new config and takes the user to the build page', async () => {
    const user = userEvent.setup();

    const response: CreateConfigurationResponse = {
      id: 'config-id',
      name: 'Anaplasmosis',
    };

    const mockMutateAsync = vi.fn().mockImplementation(
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
      mutateAsync: mockMutateAsync,
      data: { data: response },
      isLoading: false,
      isError: false,
      reset: vi.fn(),
    });

    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);

    const dialog = screen.getByRole('dialog');

    // Check to see if the modal has a class of `is-visible`.
    expect(dialog).toHaveClass('is-visible');

    const conditionInput = screen.getByLabelText('Condition');
    expect(conditionInput).toBeInTheDocument();

    await user.type(conditionInput, 'Anaplasmosis{enter}');
    expect(conditionInput).toHaveValue('Anaplasmosis');

    // try clearing the input to ensure button gets disabled
    await user.click(screen.getByTestId('combo-box-clear-button'));
    expect(screen.getByLabelText('Condition')).toHaveValue('');
    expect(
      screen.getByRole('button', {
        name: 'Add condition',
      })
    ).toBeDisabled();

    // re-enter info
    await user.type(conditionInput, 'Anaplasmosis{enter}');
    expect(conditionInput).toHaveValue('Anaplasmosis');

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeEnabled();
    await user.click(addConditionButton);

    // Check that navigation to the build page worked
    expect(
      await screen.findByText('Anaplasmosis', { selector: 'h2' })
    ).toBeInTheDocument();
    expect(screen.getByText('Next: Test configuration')).toBeInTheDocument();

    // make sure we get a success toast
    expect((await screen.findAllByText('Anaplasmosis')).length).toBeGreaterThan(
      0
    );
  });
});

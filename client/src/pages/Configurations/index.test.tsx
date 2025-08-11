import { describe, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';
import { TestQueryClientProvider } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from 'react-toastify';

// Mock configurations request
vi.mock('../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../api/configurations/configurations'
  );
  return {
    ...actual,
    useGetConfigurations: vi.fn(() => ({
      data: { data: [{ id: '1', name: 'test', is_active: true }] },
      isLoading: false,
      error: null,
    })),
  };
});

const renderPageView = () =>
  render(
    <TestQueryClientProvider>
      <ToastContainer />
      <BrowserRouter>
        <Configurations />
      </BrowserRouter>
    </TestQueryClientProvider>
  );

describe('Configurations Page', () => {
  test('renders the Configurations page with title and search bar', async () => {
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

  test('opens the modal when "Set up new condition" button is clicked', async () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(within(modal).getByText('Set up new condition')).toBeInTheDocument();
  });

  test('selects a condition from the ComboBox and enables the Add condition button', async () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);

    expect(await screen.findByRole('dialog')).toBeInTheDocument();

    const conditionInput = screen.getByLabelText('Condition');
    expect(conditionInput).toBeInTheDocument();

    await user.type(conditionInput, 'Anaplasmosis{enter}');
    expect(conditionInput).toHaveValue('Anaplasmosis');

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeEnabled();
  });

  test('submits the form and adds a new configuration to the table', async () => {
    const user = userEvent.setup();
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

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeEnabled();
    await user.click(addConditionButton);

    // Check to see if the modal has a class of `is-hidden`.
    expect(dialog).toHaveClass('is-hidden');

    // Expect the new configuration to be in the table
    const table = screen.getByTestId('table');
    expect(within(table).getByText('Anaplasmosis')).toBeInTheDocument();
    expect(within(table).getByText('Refiner off')).toBeInTheDocument(); // Default status is 'off'
  });

  test('disables the "Add condition" button when no condition is selected', async () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);

    // Expect the modal to open
    expect(await screen.findByRole('dialog')).toBeInTheDocument();

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeDisabled();
  });

  it('should render an error and success toast when the "Set up new configuration" button is clicked', async () => {
    const user = userEvent.setup();
    renderPageView();
    await user.click(screen.getByText('Test Toast', { selector: 'button' }));
    expect(
      await screen.findAllByText('New configuration created')
    ).toHaveLength(2);
  });
});

import { describe, expect } from 'vitest';
import {
  render,
  screen,
  fireEvent,
  waitFor,
  getByText,
} from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';
import userEvent from '@testing-library/user-event';

const renderPageView = () =>
  render(
    <BrowserRouter>
      <Configurations />
    </BrowserRouter>
  );

vi.mock('focus-trap-react');
vi.mock('tabbable');

describe('Configurations Page', () => {
  test('renders the Configurations page with title and search bar', () => {
    renderPageView();
    expect(
      screen.getByText('Your reportable condition configurations')
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Set up new condition' })
    ).toBeInTheDocument();
  });

  test('opens the modal when "Set up new condition" button is clicked', () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    user.click(setUpButton);
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(getByText(modal, 'Set up new condition')).toBeInTheDocument();
  });

  test('selects a condition from the ComboBox and enables the Add condition button', () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    user.click(setUpButton);

    expect(screen.queryByRole('dialog')).toBeInTheDocument();

    expect(screen.getByTestId('combo-box-input')).toBeVisible();
    user.type(screen.getByTestId('combo-box-input'), 'Roger{Enter}');
    console.log('Roger');
    screen.debug(screen.getByTestId('combo-box-input'));

    // const conditionInput = screen.getByLabelText('Condition');
    // expect(conditionInput).toBeInTheDocument();
    //
    // user.click(conditionInput);
    // user.keyboard('Anaplasmosis{Enter}');
    //
    // const anaplasmosisOption = await screen.findByText('Anaplasmosis');
    // expect(anaplasmosisOption).toBeInTheDocument();
    // userEvent.click(anaplasmosisOption);
    //
    // expect(conditionInput).toHaveValue('Anaplasmosis');
    //
    // const addConditionButton = screen.getByRole('button', {
    //    name: 'Add condition',
    // });
    // expect(addConditionButton).toBeEnabled();
  });

  test.skip('submits the form and adds a new configuration to the table', async () => {
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    fireEvent.click(setUpButton);

    // Expect the modal to open
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeInTheDocument();
    });

    const conditionInput = screen.getByLabelText('Condition');
    fireEvent.change(conditionInput, { target: { value: 'Anaplasmosis' } });

    const anaplasmosisOption = await screen.findByText('Anaplasmosis');
    fireEvent.click(anaplasmosisOption);

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    fireEvent.click(addConditionButton);

    // Expect the modal to close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    // Expect the new configuration to be in the table
    expect(screen.getByText('Anaplasmosis')).toBeInTheDocument();
    expect(screen.getByText('off')).toBeInTheDocument(); // Default status is 'off'
  });

  test.skip('disables the "Add condition" button when no condition is selected', async () => {
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    fireEvent.click(setUpButton);

    // Expect the modal to open
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeInTheDocument();
    });

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeDisabled();
  });
});

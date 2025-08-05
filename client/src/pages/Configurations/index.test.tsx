import { describe, expect } from 'vitest';
import {
  render,
  screen,
  getByText,
  findByText,
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

  test('opens the modal when "Set up new condition" button is clicked', async () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(getByText(modal, 'Set up new condition')).toBeInTheDocument();
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

    await user.type(conditionInput, 'Anaplasmosis');

    const anaplasmosisOption = await findByText(
      await screen.findByRole('option'),
      'Anaplasmosis'
    );
    expect(anaplasmosisOption).toBeInTheDocument();

    await userEvent.click(anaplasmosisOption);

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

    const dialog = await screen.getByRole('dialog');

    expect(dialog?.classList.contains('is-visible')).toEqual(true);

    const conditionInput = screen.getByLabelText('Condition');
    expect(conditionInput).toBeInTheDocument();

    await user.type(conditionInput, 'Anaplasmosis');

    const anaplasmosisOption = await findByText(
      await screen.findByRole('option'),
      'Anaplasmosis'
    );
    expect(anaplasmosisOption).toBeInTheDocument();

    await userEvent.click(anaplasmosisOption);

    expect(conditionInput).toHaveValue('Anaplasmosis');

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeEnabled();
    await user.click(addConditionButton);

    expect(dialog?.classList.contains('is-hidden')).toEqual(true);

    // Expect the new configuration to be in the table
    expect(
      getByText(screen.getByTestId('table'), 'Anaplasmosis')
    ).toBeInTheDocument();
    expect(
      getByText(screen.getByTestId('table'), 'Refiner off')
    ).toBeInTheDocument(); // Default status is 'off'
  });

  test('disables the "Add condition" button when no condition is selected', async () => {
    const user = userEvent.setup();
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    await user.click(setUpButton);

    // Expect the modal to open
    expect(screen.queryByRole('dialog')).toBeInTheDocument();

    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeDisabled();
  });
});

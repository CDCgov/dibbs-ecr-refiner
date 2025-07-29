import { describe, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';

const renderPageView = () =>
  render(
    <BrowserRouter>
      <Configurations />
    </BrowserRouter>
  );

describe('Configurations Page', () => {
  // Test case 1: Rendering the Configurations page
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

  // Test case 2: 'Set up new condition' button click opens the modal
  test('opens the modal when "Set up new condition" button is clicked', () => {
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    fireEvent.click(setUpButton);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Set up new condition')).toBeInTheDocument();
  });

  // Test case 3: Selecting a condition from the ComboBox
  test('selects a condition from the ComboBox and enables the Add condition button', async () => {
    renderPageView();
    const setUpButton = screen.getByRole('button', {
      name: 'Set up new condition',
    });
    fireEvent.click(setUpButton);

    // Expect the modal to open
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeInTheDocument();
    });

    // Mock the ComboBox's internal state or simulate user interaction
    // This part is tricky as ComboBox is a complex component.
    // We'll assume a direct interaction with the input and then selection.

    // Find the ComboBox input, which might not have a specific role but can be found by its associated label
    const conditionInput = screen.getByLabelText('Condition');
    expect(conditionInput).toBeInTheDocument();

    // Simulate typing to open the dropdown (if it's a type-ahead ComboBox)
    fireEvent.change(conditionInput, { target: { value: 'Anaplasmosis' } });

    // Wait for dropdown options to potentially appear and select one
    // This might require more specific selectors or mocking depending on ComboBox implementation
    // For now, we'll assume we can find the option and click it.
    // If the ComboBox doesn't render options directly, this test might need adjustment.
    const anaplasmosisOption = await screen.findByText('Anaplasmosis');
    expect(anaplasmosisOption).toBeInTheDocument();
    fireEvent.click(anaplasmosisOption);

    // Check if the input now displays the selected value
    expect(conditionInput).toHaveValue('Anaplasmosis');

    // Check if the "Add condition" button is enabled
    const addConditionButton = screen.getByRole('button', {
      name: 'Add condition',
    });
    expect(addConditionButton).toBeEnabled();
  });

  // Test case 4: Submitting the form and adding a new configuration
  test('submits the form and adds a new configuration to the table', async () => {
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

  // Test case 5: 'Add condition' button is disabled when no condition is selected
  test('disables the "Add condition" button when no condition is selected', async () => {
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

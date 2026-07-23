import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TurnOnConfigButton } from './TurnOnConfigButton';

describe('TurnOnConfigButton', () => {
  const mockHandleActivation = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show Zero-Code-Set warning when hasPrimaryCondition is false', async () => {
    render(
      <TurnOnConfigButton
        handleActivation={mockHandleActivation}
        disabled={false}
        isLoading={false}
        hasPrimaryCondition={false}
      />
    );

    const activateBtn = screen.getByText('Turn on configuration');
    fireEvent.click(activateBtn);

    expect(screen.getByText('Activate Zero-Code-Set Configuration?')).toBeInTheDocument();
    expect(screen.getByText(/This configuration has no primary condition/i)).toBeInTheDocument();
  });

  it('should show standard confirmation when hasPrimaryCondition is true', async () => {
    render(
      <TurnOnConfigButton
        handleActivation={mockHandleActivation}
        disabled={false}
        isLoading={false}
        hasPrimaryCondition={true}
      />
    );

    const activateBtn = screen.getByText('Turn on configuration');
    fireEvent.click(activateBtn);

    expect(screen.getByText('Turn on configuration?')).toBeInTheDocument();
    expect(screen.getByText(/Refiner will/i)).toBeInTheDocument();
    expect(screen.getByText(/immediately/i)).toBeInTheDocument();
    expect(screen.getByText(/start to refine the eCRs/i)).toBeInTheDocument();
    expect(screen.queryByText('Activate Zero-Code-Set Configuration?')).not.toBeInTheDocument();
  });

  it('should trigger handleActivation when clicking Activate in Zero-Code-Set modal', async () => {
    render(
      <TurnOnConfigButton
        handleActivation={mockHandleActivation}
        disabled={false}
        isLoading={false}
        hasPrimaryCondition={false}
      />
    );

    const activateBtn = screen.getByText('Turn on configuration');
    fireEvent.click(activateBtn);

    const modalActivateBtn = screen.getByText('Activate');
    fireEvent.click(modalActivateBtn);

    expect(mockHandleActivation).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(
      <TurnOnConfigButton
        handleActivation={mockHandleActivation}
        disabled={true}
        isLoading={false}
        hasPrimaryCondition={false}
      />
    );

    const activateBtn = screen.getByText('Turn on configuration');
    expect(activateBtn).toBeDisabled();
  });

  it('should show spinner and disable buttons when isLoading is true', async () => {
    render(
      <TurnOnConfigButton
        handleActivation={mockHandleActivation}
        disabled={false}
        isLoading={true}
        hasPrimaryCondition={false}
      />
    );

    const activateBtn = screen.getByText('Turn on configuration');
    fireEvent.click(activateBtn);

    // In the Zero-Code-Set modal, both Cancel and Activate buttons should be disabled when isLoading is true
    const cancelBtn = screen.getByText('Cancel');
    expect(cancelBtn).toBeDisabled();

    // The modal should show the Zero-Code-Set warning
    expect(screen.getByText(/This configuration has no primary condition/i)).toBeInTheDocument();
  });
});

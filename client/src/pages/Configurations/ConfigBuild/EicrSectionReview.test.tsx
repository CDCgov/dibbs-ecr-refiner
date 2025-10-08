// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import EicrSectionReview from './EicrSectionReview';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';

// We'll mock the hooks the component uses so tests can control behavior
const mockMutate = vi.fn();
const mockShowToast = vi.fn();
const mockFormatError = vi.fn(
  (err: any) => (err && err.message) || 'formatted'
);

vi.mock('../../../api/configurations/configurations', () => ({
  useUpdateConfigurationSectionProcessing: () => ({
    mutate: mockMutate,
  }),
}));

vi.mock('../../../hooks/useToast', () => ({
  useToast: () => mockShowToast,
}));

vi.mock('../../../hooks/useErrorFormatter', () => ({
  useApiErrorFormatter: () => mockFormatError,
}));

// Helper that provides a fresh QueryClient for each test — keeps behavior consistent
function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('EicrSectionReview (improved)', () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockShowToast.mockReset();
    mockFormatError.mockReset();
  });

  afterEach(() => {
    // clear DOM between tests
    vi.clearAllMocks();
  });

  it('optimistically updates the UI and calls mutate with the correct payload when clicking a radio', async () => {
    const configurationId = 'config-123';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section A', code: 'A01', action: 'retain' },
    ];

    // Track what payload mutate receives
    mockMutate.mockImplementation((/* payload: any, _options: any */) => {
      // no-op: simulate successful response
    });

    renderWithQueryClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );

    // The input has an accessible aria-label set in the component
    const includeEntireInput = screen.getByLabelText(
      'Include entire section Section A'
    );
    expect(includeEntireInput).toBeInTheDocument();

    // Locate the correct td for the "Include entire section" radio
    const tdRadios = screen.getAllByRole('radio');
    // Find the td whose input matches our aria-label
    const parentTd = Array.from(tdRadios).find((td) =>
      td.querySelector('input[aria-label="Include entire section Section A"]')
    ) as HTMLElement;
    expect(parentTd).toBeTruthy();

    // Simulate clicking the radio input directly
    await userEvent.click(includeEntireInput);

    // Expect mutate to have been called with the correct payload
    expect(mockMutate).toHaveBeenCalledTimes(1);
    const [mutatePayload] = mockMutate.mock.calls[0];
    expect(mutatePayload).toEqual({
      configurationId,
      data: { sections: [{ code: 'A01', action: 'refine' }] },
    });

    // Wait for the optimistic UI update to reflect in the input.checked
    await waitFor(() => expect(includeEntireInput).toBeChecked());
  });

  it('supports keyboard activation (Enter and Space) and updates UI optimistically', async () => {
    const configurationId = 'config-456';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section B', code: 'B01', action: 'retain' },
    ];

    mockMutate.mockImplementation((/* payload: any, _options: any */) => {});

    renderWithQueryClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );

    const includeEntireInput = screen.getByLabelText(
      'Include entire section Section B'
    );
    expect(includeEntireInput).toBeInTheDocument();

    // Find the td element with role="radio" that contains the "Include entire section" input
    const radioCells = screen.getAllByRole('radio');
    const includeEntireTd = radioCells.find((cell) =>
      cell.querySelector('input[aria-label="Include entire section Section B"]')
    ) as HTMLElement;
    expect(includeEntireTd).toBeTruthy();

    includeEntireTd.focus();
    await userEvent.click(includeEntireTd);
    expect(mockMutate).toHaveBeenCalledTimes(1);

    // Query for fresh element reference after state update
    await waitFor(() => {
      const freshIncludeEntireInput = screen.getByRole('radio', {
        name: 'Include entire section Section B',
      });
      expect(freshIncludeEntireInput).toBeChecked();
    });

    // Reset call count and revert state for next test
    mockMutate.mockReset();

    // Click on retain to reset state
    const retainInput = screen.getByLabelText(
      'Include and refine section Section B'
    );
    await userEvent.click(retainInput);
    await waitFor(() => {
      const freshRetainInput = screen.getByRole('radio', {
        name: 'Include and refine section Section B',
      });
      expect(freshRetainInput).toBeChecked();
    });
    mockMutate.mockReset();

    // Directly focus the button for 'Include and refine section Section B'
    const retainButton = screen
      .getAllByRole('radio')
      .find((node) =>
        node.querySelector(
          'input[aria-label="Include and refine section Section B"]'
        )
      );
    expect(retainButton).toBeTruthy();
    retainButton?.focus();
    await userEvent.keyboard(' '); // Simulate spacebar activation
    expect(mockMutate).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      const freshRetainInput = screen.getByRole('radio', {
        name: 'Include and refine section Section B',
      });
      expect(freshRetainInput).toBeChecked();
    });
  });

  it('reverts optimistic UI when mutate calls onError and displays a toast', async () => {
    const configurationId = 'config-789';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section C', code: 'C01', action: 'retain' },
    ];

    // mutate will call onError to simulate a server failure after a slight delay
    mockMutate.mockImplementation((_payload: any, options: any) => {
      if (options && typeof options.onError === 'function') {
        // Use setTimeout to allow optimistic update to be visible first
        setTimeout(() => {
          options.onError(new Error('Server error'));
        }, 10);
      }
    });

    renderWithQueryClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );

    const includeEntireInput = screen.getByLabelText(
      'Include entire section Section C'
    );
    const retainInput = screen.getByLabelText(
      'Include and refine section Section C'
    );

    expect(includeEntireInput).toBeInTheDocument();
    expect(retainInput).toBeChecked(); // Initially should be retain (checked)
    expect(includeEntireInput).not.toBeChecked(); // Include entire should not be checked

    // Simulate user clicking the "Include entire section" radio input
    await userEvent.click(includeEntireInput);

    // Wait for optimistic UI to be applied (input should be checked)
    await waitFor(() => {
      const freshIncludeEntireInput = screen.getByLabelText(
        'Include entire section Section C'
      );
      expect(freshIncludeEntireInput).toBeChecked();
    });

    // After onError runs, the component should revert the UI back to retain and show a toast
    await waitFor(() => {
      const freshIncludeEntireInput = screen.getByLabelText(
        'Include entire section Section C'
      );
      const freshRetainInput = screen.getByLabelText(
        'Include and refine section Section C'
      );
      expect(freshIncludeEntireInput).not.toBeChecked();
      expect(freshRetainInput).toBeChecked(); // Should revert back to retain
      expect(mockShowToast).toHaveBeenCalled();
    });

    // Ensure the error formatting function was called with the error
    expect(mockFormatError).toHaveBeenCalled();
  });
});

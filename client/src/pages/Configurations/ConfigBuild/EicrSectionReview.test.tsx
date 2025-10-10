// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import EicrSectionReview from './EicrSectionReview';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';

const mockMutate = vi.fn();
const mockShowToast = vi.fn();
const mockFormatError = vi.fn(
  (err: any) => (err && err.message) || 'formatted'
);

vi.mock('../../../api/configurations/configurations', () => ({
  useUpdateConfigurationSectionProcessing: () => ({ mutate: mockMutate }),
}));
vi.mock('../../../hooks/useToast', () => ({ useToast: () => mockShowToast }));
vi.mock('../../../hooks/useErrorFormatter', () => ({
  useApiErrorFormatter: () => mockFormatError,
}));

/**
 * Helper for rendering with a fresh QueryClient per test.
 */
function renderWithClient(ui: React.ReactElement) {
  return render(<TestQueryClientProvider>{ui}</TestQueryClientProvider>);
}

describe('EicrSectionReview accessibility & behavior', () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockShowToast.mockReset();
    mockFormatError.mockReset();
  });
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('optimistically updates UI and calls mutate on radio activation via cell click', async () => {
    const configurationId = 'config-1';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section X', code: 'X01', action: 'retain' },
    ];
    renderWithClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );
    // Find the radio for 'Include entire section' and click its parent cell
    const input = screen.getByLabelText('Include entire section Section X');
    expect(input).not.toBeChecked();
    // Find the <td> cell containing the input (cell handles click)
    const cell = screen
      .getAllByRole('cell')
      .find((cell) =>
        cell.querySelector(
          'input[aria-label="Include entire section Section X"]'
        )
      );
    expect(cell).toBeTruthy();
    await userEvent.click(cell!);
    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate.mock.calls[0][0]).toMatchObject({
      configurationId,
      data: { sections: [{ code: 'X01', action: 'refine' }] },
    });
    await waitFor(() =>
      expect(
        screen.getByLabelText('Include entire section Section X')
      ).toBeChecked()
    );
  });

  it('supports keyboard activation (Enter/Space) on correct cell', async () => {
    const configurationId = 'config-2';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section Y', code: 'Y01', action: 'retain' },
    ];
    renderWithClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );
    // Find cell for 'Include entire section'
    const cell = screen
      .getAllByRole('cell')
      .find((cell) =>
        cell.querySelector(
          'input[aria-label="Include entire section Section Y"]'
        )
      );
    expect(cell).toBeTruthy();
    cell!.focus();
    await userEvent.keyboard('{Enter}');
    expect(mockMutate).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(
        screen.getByLabelText('Include entire section Section Y')
      ).toBeChecked()
    );

    // Reset back to retain
    mockMutate.mockReset();
    const retainCell = screen
      .getAllByRole('cell')
      .find((cell) =>
        cell.querySelector(
          'input[aria-label="Include and refine section Section Y"]'
        )
      );
    expect(retainCell).toBeTruthy();
    retainCell!.focus();
    await userEvent.keyboard(' ');
    expect(mockMutate).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(
        screen.getByLabelText('Include and refine section Section Y')
      ).toBeChecked()
    );
  });

  it('reverts optimistic UI and shows toast on API error', async () => {
    const configurationId = 'config-3';
    const sections: DbConfigurationSectionProcessing[] = [
      { name: 'Section Z', code: 'Z01', action: 'retain' },
    ];
    mockMutate.mockImplementation((_payload: any, options: any) => {
      setTimeout(() => {
        options?.onError?.(new Error('Server error'));
      }, 10);
    });
    renderWithClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
      />
    );
    // Find target cell
    const cell = screen
      .getAllByRole('cell')
      .find((cell) =>
        within(cell).queryByLabelText('Include entire section Section Z')
      );
    expect(cell).toBeTruthy();
    await userEvent.click(cell!);
    // Assert optimistic UI: radio is checked (wait for optimistic update to appear)
    expect(
      await screen.findByLabelText('Include entire section Section Z')
    ).toBeChecked();
    // Now wait for error and assert UI reverts, toast called
    await waitFor(() => {
      expect(
        screen.getByLabelText('Include entire section Section Z')
      ).not.toBeChecked();
      expect(
        screen.getByLabelText('Include and refine section Section Z')
      ).toBeChecked();
      expect(mockShowToast).toHaveBeenCalled();
      expect(mockFormatError).toHaveBeenCalled();
    });
  });
});

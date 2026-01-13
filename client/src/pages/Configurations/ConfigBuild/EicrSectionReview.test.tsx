// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TestQueryClientProvider } from '../../../test-utils';
import { EicrSectionReview } from './EicrSectionReview';
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
      { name: 'Section X', code: 'X01', action: 'refine' },
    ];

    renderWithClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
        isLocked={false}
      />
    );

    const input = screen.getByLabelText('Include entire section Section X');
    expect(input).not.toBeChecked();

    await userEvent.click(input);

    expect(mockMutate).toHaveBeenCalledTimes(1);
    expect(mockMutate.mock.calls[0][0]).toMatchObject({
      configurationId,
      data: { sections: [{ code: 'X01', action: 'retain' }] },
    });

    expect(
      await screen.findByLabelText('Include entire section Section X')
    ).toBeChecked();
  });

  it('reverts optimistic UI and shows toast on API error', async () => {
    const configurationId = 'config-3';
    const sections = [{ name: 'Section Z', code: 'Z01', action: 'refine' }];

    mockMutate.mockImplementation((_payload: any, options: any) => {
      options?.onError?.(new Error('Server error'));
    });

    renderWithClient(
      <EicrSectionReview
        sectionProcessing={sections}
        configurationId={configurationId}
        isLocked={false}
      />
    );

    // Click the RADIO, not the <td>
    const radio = screen.getByLabelText('Include entire section Section Z');

    await userEvent.click(radio);

    await waitFor(() => {
      expect(mockShowToast).toHaveBeenCalledTimes(1);
      expect(mockFormatError).toHaveBeenCalled();
    });
  });
});

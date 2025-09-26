import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import ConfigActivate from '.';
import { TestQueryClientProvider } from '../../../test-utils';
import {
  Condition,
  DbConfigurationCustomCode,
  DbTotalConditionCodeCount,
  HTTPValidationError,
} from '../../../api/schemas';
import userEvent from '@testing-library/user-event';
import { useRunInlineConfigurationTest } from '../../../api/configurations/configurations';
import { Mock } from 'vitest';
import { AxiosError } from 'axios';

// Mock all API requests.
const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
  { condition_id: 'chlamydia-1', display_name: 'Chlamydia', total_codes: 8 },
  { condition_id: 'gonorrhea-1', display_name: 'Gonorrhea', total_codes: 5 },
];

const mockCustomCodes: DbConfigurationCustomCode[] = [
  { code: 'custom-code1', name: 'test-custom-code1', system: 'ICD-10' },
];

const mockMatchedCondition: Condition = {
  code: '840539006',
  display_name: 'COVID-19',
  refined_eicr: '<xml>refined covid</xml>',
  stats: ['eICR file reduced by 71%'],
};

const mockSuccessfulInlineTestResponse = {
  data: {
    condition: mockMatchedCondition,
    original_eicr: '<xml>unrefined covid</xml>',
    refined_download_url: 'http://mocks3download.com',
  },
};

// Mock configurations request
vi.mock('../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useAddCustomCodeToConfiguration: vi.fn(),
    useDeleteCustomCodeFromConfiguration: vi.fn(),
    useEditCustomCodeFromConfiguration: vi.fn(),
    useGetConfiguration: vi.fn(() => ({
      data: {
        data: {
          id: 'config-id',
          display_name: 'COVID-19',
          code_sets: mockCodeSets,
          custom_codes: mockCustomCodes,
          included_conditions: [
            { id: 'covid-1', display_name: 'COVID-19', associated: true },
            { id: 'chlamydia-1', display_name: 'Chlamydia', associated: false },
            { id: 'gonorrhea-1', display_name: 'Gonorrhea', associated: false },
          ],
        },
      },
      isLoading: false,
      isError: false,
    })),
    useRunInlineConfigurationTest: vi.fn(() => ({
      mutateAsync: vi.fn().mockResolvedValue({ data: {} }),
      reset: vi.fn(),
      data: {
        data: {
          condition: mockMatchedCondition,
          original_eicr: '<xml>unrefined covid</xml>',
          refined_download_url: 'http://mocks3download.com',
        },
      },
      isLoading: false,
      isError: false,
    })),
  };
});

describe('Config testing page', () => {
  function renderPage() {
    return render(
      <TestQueryClientProvider>
        <MemoryRouter initialEntries={['/configurations/config-id/test']}>
          <Routes>
            <Route
              path="/configurations/:id/test"
              element={<ConfigActivate />}
            />
          </Routes>
        </MemoryRouter>
      </TestQueryClientProvider>
    );
  }

  it('should show "Test configuration" as the current step', () => {
    renderPage();
    expect(
      screen.getByText('Build configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Test configuration', { selector: 'a' })
    ).toHaveAttribute('aria-current', 'page');
    expect(
      screen.getByText('Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();
  });

  it('should warn the user that the expected condition was not found during inline testing', async () => {
    const user = userEvent.setup();

    const warningMessage =
      'Condition was not detected in the eCR file you uploaded.';

    (useRunInlineConfigurationTest as unknown as Mock).mockImplementation(
      ({ mutation }) => {
        return {
          mutateAsync: vi.fn().mockImplementation(() => {
            const error = new AxiosError<HTTPValidationError>();
            error.response = {
              data: { detail: warningMessage },
            } as any;

            // trigger your mutation onError callback
            mutation?.onError?.(error);

            // reject so the hook enters error state
            return Promise.reject(error);
          }),
          reset: vi.fn(),
          data: null,
        };
      }
    );

    renderPage();

    // check initial screen
    expect(
      screen.getByText('Next: Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();

    // mock the upload
    await user.click(screen.getByText('Use test file'));

    // find warning screen elements
    expect(await screen.findByText(warningMessage)).toBeInTheDocument();
    expect(await screen.findByText('Try again')).toBeInTheDocument();
  });

  it('should allow config testing using inline testing flow', async () => {
    const user = userEvent.setup();

    (useRunInlineConfigurationTest as unknown as Mock).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(mockSuccessfulInlineTestResponse),
      data: mockSuccessfulInlineTestResponse,
    });

    renderPage();

    // check initial screen
    expect(
      screen.getByText('Next: Turn on configuration', { selector: 'a' })
    ).toBeInTheDocument();
    expect(
      screen.getByText('Want to refine your own eCR file?')
    ).toBeInTheDocument();
    expect(screen.getByText("Don't have a file ready?")).toBeInTheDocument();

    // mock the upload
    await user.click(screen.getByText('Use test file'));

    // Check success page
    expect(
      await screen.findByText('eICR file reduced by 71%')
    ).toBeInTheDocument();
    expect(screen.getByText('Original eICR')).toBeInTheDocument();
    expect(screen.getByText('Refined eICR')).toBeInTheDocument();
  });
});

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Demo from '.';
import { BrowserRouter } from 'react-router';
import { useUploadEcr } from '../../api/demo/demo.ts';
import { RefinedTestingDocument } from '../../api/schemas/refinedTestingDocument.ts';
import { Mock } from 'vitest';
import { useGetEnv } from '../../hooks/useGetEnv.ts';

vi.mock('../../api/demo/demo', () => ({ useUploadEcr: vi.fn() }));

vi.mock('../../hooks/useGetEnv', () => ({
  useGetEnv: vi.fn(() => 'local'),
}));

const mockUploadResponse: RefinedTestingDocument = {
  conditions: [
    {
      code: 'mock-code',
      display_name: 'mock condition name',
      refined_eicr: '<data>less data</data>',
      stats: ['eICR reduced by 59%'],
    },
  ],
  conditions_found: 1,
  processing_notes: ['Testing notes'],
  message: 'test message',
  unrefined_eicr: '<data>tons of data here</data>',
  refined_download_url: 'http://s3-standard.com',
};

const mockCustomUploadResponse: RefinedTestingDocument = {
  conditions: [
    {
      code: 'mock-custom-file',
      display_name: 'custom condition',
      refined_eicr: '<data>refined custom data</data>',
      stats: ['eICR reduced by 77%'],
    },
  ],
  conditions_found: 1,
  processing_notes: ['Testing notes'],
  message: 'test message',
  unrefined_eicr: '<data>unrefined custom data</data>',
  refined_download_url: 'http://s3-custom.com',
};

const renderDemoView = () =>
  render(
    <BrowserRouter>
      <Demo />
    </BrowserRouter>
  );

describe('Demo', () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should navigate the demo flow using the sample file', async () => {
    const user = userEvent.setup();

    const mockMutateAsync = vi.fn().mockResolvedValue({
      status: 200,
      data: mockUploadResponse,
    });

    // navigate to reportable conditions
    (useUploadEcr as unknown as Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      data: { data: mockUploadResponse },
      reset: vi.fn(),
    });

    renderDemoView();

    // check that we start on the "run test" page
    expect(
      screen.getByText('You can try out eCR Refiner with our test file.')
    ).toBeInTheDocument();

    await user.click(screen.getByText('Use test file'));

    expect(useUploadEcr).toHaveBeenCalled();
    expect(mockMutateAsync).toHaveBeenCalledOnce();

    // check reportable conditions view
    expect(
      screen.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('mock condition name')).toBeInTheDocument();
    await user.click(screen.getByText('Refine eCR', { selector: 'button' }));

    // check success page
    expect(screen.getByText('eCR refinement results')).toBeInTheDocument();
    expect(screen.getByText('eICR reduced by 59%')).toBeInTheDocument();
  });

  it('should navigate the demo flow using an uploaded zip file', async () => {
    const user = userEvent.setup();

    const mockMutateAsync = vi.fn().mockResolvedValue({
      status: 200,
      data: mockCustomUploadResponse,
    });

    // navigate to reportable conditions
    (useUploadEcr as unknown as Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      data: { data: mockCustomUploadResponse },
      reset: vi.fn(),
    });

    renderDemoView();

    // check that we start on the "run test" page
    expect(screen.getByText('Select .zip file')).toBeInTheDocument();

    const file = new File(['test'], 'test.zip', { type: 'application/zip' });
    const input: HTMLInputElement = screen.getByLabelText('Select .zip file');

    // upload the file
    await user.upload(input, file);

    // check that the input's file list looks correct
    expect(input.files).toHaveLength(1);
    expect(input.files?.item(0)).toBe(file);
    expect(input.files?.[0]).toBe(file);

    // check that the screen updated with new options
    expect(screen.getByText('test.zip')).toBeInTheDocument();
    expect(screen.getByText('Change file')).toBeInTheDocument();
    expect(screen.getByText('Upload .zip file')).toBeInTheDocument();

    // run the refine process on the custom file
    await user.click(screen.getByText('Upload .zip file'));
    expect(mockMutateAsync).toHaveBeenCalledOnce();

    // check reportable conditions view
    expect(
      screen.getByText(
        'We found the following reportable condition(s) in the RR:'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('custom condition')).toBeInTheDocument();
    await user.click(screen.getByText('Refine eCR', { selector: 'button' }));

    // check success page
    expect(screen.getByText('eCR refinement results')).toBeInTheDocument();
    expect(screen.getByText('eICR reduced by 77%')).toBeInTheDocument();
  });

  it('should navigate to the error view when the upload request fails', async () => {
    type MutationParam = {
      onError?: (error: Error) => void;
    };

    const user = userEvent.setup();

    // throw an error when called
    (useUploadEcr as unknown as Mock).mockImplementation(
      ({ mutation }: { mutation?: MutationParam }) => {
        return {
          mutateAsync: vi.fn().mockImplementation(() => {
            const error = new Error('API call failed') as Error & {
              response: { data: { detail: string } };
            };

            error.response = { data: { detail: 'Server is down' } };

            if (mutation?.onError) {
              mutation.onError(error);
            }

            throw error;
          }),
          reset: vi.fn(),
        };
      }
    );

    renderDemoView();

    await user.click(screen.getByText('Use test file'));

    // check that we made it to the error view
    expect(
      await screen.findByText(
        'Please double check the format and size. It must be less than 10MB in size.'
      )
    ).toBeInTheDocument();

    // Server error should be shown to the user
    expect(
      await screen.findByText('Error: Server is down')
    ).toBeInTheDocument();

    // return to the start to try again
    await user.click(await screen.findByText('Try again'));
    expect(
      await screen.findByText('Use test file', { selector: 'button' })
    ).toBeInTheDocument();
  });
});

it('should show PHI/PII banner in the "local" environment', () => {
  (useUploadEcr as unknown as Mock).mockImplementation(() => {
    return {
      mutateAsync: vi.fn().mockImplementation(() => {}),
      reset: vi.fn(),
    };
  });

  const bannerText = 'This environment is not approved to handle PHI/PII.';
  (useGetEnv as unknown as Mock).mockReturnValue('local');

  renderDemoView();
  expect(screen.getByText(bannerText)).toBeInTheDocument();
});

it('should show PHI/PII banner in the "demo" environment', () => {
  (useUploadEcr as unknown as Mock).mockImplementation(() => {
    return {
      mutateAsync: vi.fn().mockImplementation(() => {}),
      reset: vi.fn(),
    };
  });

  const bannerText = 'This environment is not approved to handle PHI/PII.';
  (useGetEnv as unknown as Mock).mockReturnValue('demo');

  renderDemoView();
  expect(screen.getByText(bannerText)).toBeInTheDocument();
});

it('should NOT show PHI/PII banner in the "prod" environment', () => {
  (useUploadEcr as unknown as Mock).mockImplementation(() => {
    return {
      mutateAsync: vi.fn().mockImplementation(() => {}),
      reset: vi.fn(),
    };
  });

  const bannerText = 'This environment is not approved to handle PHI/PII.';
  (useGetEnv as unknown as Mock).mockReturnValue('prod');

  renderDemoView();
  expect(screen.queryByText(bannerText)).not.toBeInTheDocument();
});

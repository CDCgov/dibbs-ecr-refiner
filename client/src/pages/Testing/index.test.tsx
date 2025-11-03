import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Demo from '.';
import { BrowserRouter } from 'react-router';
import { useUploadEcr } from '../../api/demo/demo.ts';
import { Mock } from 'vitest';
import { useGetEnv } from '../../hooks/useGetEnv.ts';
import { IndependentTestUploadResponse } from '../../api/schemas/independentTestUploadResponse.ts';
import { ERROR_UPLOAD_MESSAGE } from '../../components/FileUploadWarning/index.tsx';
import { uploadTestFile } from '../Configurations/ConfigTest/index.test.tsx';
import { AxiosError } from 'axios';

vi.mock('../../api/demo/demo', () => ({ useUploadEcr: vi.fn() }));

vi.mock('../../hooks/useGetEnv', () => ({
  useGetEnv: vi.fn(() => 'local'),
}));

const mockTestFile = new File(['test'], 'test.zip', { type: 'text/plain' });

const mockUploadResponse: IndependentTestUploadResponse = {
  refined_conditions: [
    {
      code: 'mock-code',
      display_name: 'mock condition name',
      refined_eicr: '<data>less data</data>',
      refined_rr: '<data>less data</data>',
      stats: ['eICR reduced by 59%'],
    },
  ],
  conditions_without_matching_configs: [],
  refined_conditions_found: 1,
  message: 'test message',
  unrefined_eicr: '<data>tons of data here</data>',
  refined_download_url: 'http://s3-standard.com',
};

const mockCustomUploadResponse: IndependentTestUploadResponse = {
  refined_conditions: [
    {
      code: 'mock-custom-file',
      display_name: 'custom condition',
      refined_eicr: '<data>refined custom data</data>',
      stats: ['eICR reduced by 77%'],
    },
  ],
  conditions_without_matching_configs: [],
  refined_conditions_found: 1,
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
      screen.getByText('Want to refine your own eCR file?')
    ).toBeInTheDocument();

    await uploadTestFile(user);

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
    expect(screen.getByText('Upload .zip file')).toBeInTheDocument();

    const file = new File(['test'], 'test.zip', { type: 'application/zip' });
    const input: HTMLInputElement = screen.getByLabelText('Upload .zip file');

    // upload the file
    await user.upload(input, file);

    // check that the input's file list looks correct
    expect(input.files).toHaveLength(1);
    expect(input.files?.item(0)).toBe(file);
    expect(input.files?.[0]).toBe(file);

    // check that the screen updated with new options
    expect(screen.getByText('test.zip')).toBeInTheDocument();
    expect(screen.getByText('Change file')).toBeInTheDocument();
    expect(screen.getByText('Refine .zip file')).toBeInTheDocument();

    // run the refine process on the custom file
    await user.click(screen.getByText('Refine .zip file'));
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
            const error = new AxiosError('API call failed') as Error & {
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

    await uploadTestFile(user);

    // check that we made it to the error view
    expect(await screen.findByText(ERROR_UPLOAD_MESSAGE)).toBeInTheDocument();

    // Server error should be shown to the user
    expect(await screen.findByText('Server is down')).toBeInTheDocument();

    // return to the start to try again
    await user.click(await screen.findByText('Try again'));
    expect(
      await screen.findByText('Refine .zip file', { selector: 'button' })
    ).toBeInTheDocument();
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

  it('should let the user know that no conditions reportable to their JD ID were found in the RR', async () => {
    const user = userEvent.setup();

    (useUploadEcr as unknown as Mock).mockImplementation(() => {
      return {
        mutateAsync: vi.fn(),
        data: {
          data: {
            refined_conditions: [],
            conditions_without_matching_configs: [],
          },
        },
      };
    });

    renderDemoView();

    await uploadTestFile(user);
    // only start over button is available
    expect(await screen.findByText('Start over')).toBeInTheDocument();
    expect(screen.queryByText('Refine eCR')).not.toBeInTheDocument();

    expect(
      screen.getByText(
        'No conditions reportable to your jurisdiction were found in the RR.'
      )
    ).toBeInTheDocument();
  });

  it('should display only reportable conditions with missing configurations', async () => {
    const user = userEvent.setup();

    (useUploadEcr as unknown as Mock).mockImplementation(() => {
      return {
        mutateAsync: vi.fn(),
        data: {
          data: {
            refined_conditions: [],
            conditions_without_matching_configs: ['Influenza'],
          },
        },
      };
    });

    renderDemoView();
    await uploadTestFile(user);

    // only start over button is available
    expect(await screen.findByText('Start over')).toBeInTheDocument();
    expect(screen.queryByText('Refine eCR')).not.toBeInTheDocument();

    // only missing condition text is in the doc
    expect(
      screen.getByText(
        'Please either create configurations for these conditions or upload a file that includes conditions that have been configured.'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('Influenza')).toBeInTheDocument();
    expect(
      screen.queryByText('Would you like to refine the eCR?')
    ).not.toBeInTheDocument();
  });

  it('should display only reportable conditions that have a matching configuration', async () => {
    const user = userEvent.setup();

    (useUploadEcr as unknown as Mock).mockImplementation(() => {
      return {
        mutateAsync: vi.fn(),
        data: {
          data: {
            refined_conditions: [
              {
                code: '840539006',
                display_name: 'COVID-19',
                refined_eicr: '<xml>mock</xml>',
                stats: ['eICR reduced by XY%'],
              },
            ],
            conditions_without_matching_configs: [],
          },
        },
      };
    });

    renderDemoView();
    await uploadTestFile(user);

    // Both buttons should be available
    expect(screen.getByText('Start over')).toBeInTheDocument();
    expect(screen.getByText('Refine eCR')).toBeInTheDocument();

    // Missing config text should not be present
    expect(
      screen.queryByText(
        'Please either create configurations for these conditions or upload a file that includes conditions that have been configured.'
      )
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText('Would you like to refine the eCR?')
    ).toBeInTheDocument();
  });

  it('should display reportable conditions with both missing and matching configurations', async () => {
    const user = userEvent.setup();

    (useUploadEcr as unknown as Mock).mockImplementation(() => {
      return {
        mutateAsync: vi.fn(),
        data: {
          data: {
            refined_conditions: [
              {
                code: '840539006',
                display_name: 'COVID-19',
                refined_eicr: '<xml>mock</xml>',
                stats: ['eICR reduced by XY%'],
              },
            ],
            conditions_without_matching_configs: ['Influenza'],
          },
        },
      };
    });

    renderDemoView();

    const input = screen.getByTestId('zip-upload-input');
    await user.upload(input, mockTestFile);

    // Both buttons should be available
    expect(screen.getByText('Change file')).toBeInTheDocument();
    expect(screen.getByText('Refine .zip file')).toBeInTheDocument();

    await user.click(screen.getByText('Refine .zip file'));

    // Missing config warning should be present
    expect(
      screen.queryByText(
        'The following detected conditions have not been configured and will not produce a refined eICR in the output.'
      )
    ).toBeInTheDocument();

    // Text asking to refine should be available
    expect(
      screen.queryByText('Would you like to refine the eCR?')
    ).toBeInTheDocument();
  });
});

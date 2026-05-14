import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Testing } from '.';
import { MemoryRouter } from 'react-router';
import {
  useDiscoverConfigurations,
  useUploadEcr,
} from '../../api/demo/demo.ts';
import { Mock } from 'vitest';
import { IndependentTestUploadResponse } from '../../api/schemas/independentTestUploadResponse.ts';
import { ERROR_UPLOAD_MESSAGE } from '@components/FileUploadWarning/index.tsx';
import { uploadTestFile } from '../Configurations/ConfigTest/index.test.tsx';
import { AxiosError } from 'axios';
import { TestQueryClientProvider } from '../../test-utils.tsx';
import { FileInfoResponseValue } from '../../api/schemas/fileInfoResponse.ts';
import { DiscoveredConfigurationsResponse } from '../../api/schemas/discoveredConfigurationsResponse.ts';

vi.mock('../../api/demo/demo', () => ({
  useUploadEcr: vi.fn(),
  useDiscoverConfigurations: vi.fn(),
}));

vi.mock('../../hooks/useGetEnv', () => ({
  useGetEnv: vi.fn(() => 'local'),
}));

const mockTestFile = new File(['test'], 'test.zip', { type: 'text/plain' });

const mockConfigDiscoveryResponse: DiscoveredConfigurationsResponse = {
  groups: [
    {
      name: 'COVID-19',
      condition_id: '2da5c712-6dc6-4ddf-8d1a-e34c0e77913a',
      versions: [
        {
          id: '4b7900b7-6f09-4ad5-bb94-49d5868d7a9a',
          version: 1,
          status: 'draft',
        },
      ],
    },
    {
      name: 'Influenza',
      condition_id: '9bf9da1a-10a8-487c-8bcf-85a55ad229dd',
      versions: [
        {
          id: '5b7900b7-6f09-4ad5-bb94-49d5868d7a9a',
          version: 1,
          status: 'active',
        },
      ],
    },
  ],
};

const mockUploadResponse: IndependentTestUploadResponse = {
  refined_conditions: [
    {
      code: 'mock-code',
      display_name: 'mock condition name',
      refined_eicr: '<data>less data</data>',
      stats: ['eICR reduced by 59%'],
      render_diff: true,
    },
  ],
  refined_conditions_found: 1,
  message: 'test message',
  unrefined_eicr: '<data>tons of data here</data>',
  refined_download_key: '43ca0ec6-d280-434c-9bbc-c3b3dd51e94e_refined_ecr.zip',
  file_info_response: FileInfoResponseValue,
};

const mockCustomUploadResponse: IndependentTestUploadResponse = {
  refined_conditions: [
    {
      code: 'mock-custom-file',
      display_name: 'custom condition',
      refined_eicr: '<data>refined custom data</data>',
      stats: ['eICR reduced by 77%'],
      render_diff: true,
    },
  ],
  refined_conditions_found: 1,
  message: 'test message',
  unrefined_eicr: '<data>unrefined custom data</data>',
  refined_download_key: 'de3858c7-28a7-487c-ad7a-3853a8356811_refined_ecr.zip',
  file_info_response: FileInfoResponseValue,
};

const renderView = () =>
  render(
    <MemoryRouter>
      <TestQueryClientProvider>
        <Testing />
      </TestQueryClientProvider>
    </MemoryRouter>
  );

describe('Independent testing', () => {
  describe('Independent testing - errors during config discovery', () => {
    beforeEach(() => {
      (useDiscoverConfigurations as unknown as Mock).mockReturnValue({
        mutateAsync: vi.fn().mockResolvedValue({
          status: 200,
          data: mockConfigDiscoveryResponse,
        }),
        data: { data: mockConfigDiscoveryResponse },
        reset: vi.fn(),
      });

      (useUploadEcr as unknown as Mock).mockReturnValue({
        mutateAsync: vi.fn(),
        data: undefined,
        reset: vi.fn(),
      });
    });

    afterEach(() => {
      vi.resetAllMocks();
    });

    it('should navigate to the error view when the upload request fails', async () => {
      type MutationParam = {
        onError?: (error: Error) => void;
      };

      const user = userEvent.setup();

      (useDiscoverConfigurations as unknown as Mock).mockImplementation(
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

      renderView();
      await uploadTestFile(user);

      expect(await screen.findByText(ERROR_UPLOAD_MESSAGE)).toBeInTheDocument();
      expect(await screen.findByText('Server is down')).toBeInTheDocument();

      await user.click(await screen.findByText('Try again'));

      expect(
        await screen.findByText('Refine .zip file', { selector: 'button' })
      ).toBeInTheDocument();
    });

    it('should let the user know that no conditions reportable to their JD ID were found in the RR', async () => {
      const user = userEvent.setup();

      (useDiscoverConfigurations as unknown as Mock).mockReturnValue({
        mutateAsync: vi.fn(),
        data: {
          data: {
            groups: [],
          },
        },
        reset: vi.fn(),
      });

      renderView();
      await uploadTestFile(user);

      expect(await screen.findByText('Start over')).toBeInTheDocument();
      expect(screen.queryByText('Refine eCR')).not.toBeInTheDocument();
      expect(
        screen.getByText(
          'No conditions reportable to your jurisdiction were found in the RR.'
        )
      ).toBeInTheDocument();
    });
  });

  // describe('Independent testing - errors during refinement', () => {
  //   beforeEach(() => {
  //     (useDiscoverConfigurations as unknown as Mock).mockReturnValue({
  //       mutateAsync: vi.fn().mockResolvedValue({
  //         status: 200,
  //         data: mockConfigDiscoveryResponse,
  //       }),
  //       data: { data: mockConfigDiscoveryResponse },
  //       reset: vi.fn(),
  //     });

  //     (useUploadEcr as unknown as Mock).mockReturnValue({
  //       mutateAsync: vi.fn(),
  //       data: undefined,
  //       reset: vi.fn(),
  //     });
  //   });

  //   afterEach(() => {
  //     vi.resetAllMocks();
  //   });

  //   it('should navigate to the error view when the upload request fails', async () => {
  //     type MutationParam = {
  //       onError?: (error: Error) => void;
  //     };

  //     const user = userEvent.setup();

  //     (useUploadEcr as unknown as Mock).mockImplementation(
  //       ({ mutation }: { mutation?: MutationParam }) => {
  //         return {
  //           mutateAsync: vi.fn().mockImplementation(() => {
  //             const error = new AxiosError('API call failed') as Error & {
  //               response: { data: { detail: string } };
  //             };
  //             error.response = { data: { detail: 'Server is down' } };
  //             if (mutation?.onError) {
  //               mutation.onError(error);
  //             }
  //             throw error;
  //           }),
  //           reset: vi.fn(),
  //         };
  //       }
  //     );

  //     renderView();
  //     await uploadTestFile(user);

  //     expect(await screen.findByText(ERROR_UPLOAD_MESSAGE)).toBeInTheDocument();
  //     expect(await screen.findByText('Server is down')).toBeInTheDocument();

  //     await user.click(await screen.findByText('Try again'));

  //     expect(
  //       await screen.findByText('Refine .zip file', { selector: 'button' })
  //     ).toBeInTheDocument();
  //   });

  //   it('should let the user know that no conditions reportable to their JD ID were found in the RR', async () => {
  //     const user = userEvent.setup();

  //     (useDiscoverConfigurations as unknown as Mock).mockReturnValue({
  //       mutateAsync: vi.fn(),
  //       data: {
  //         data: {
  //           refined_conditions: [],
  //         },
  //       },
  //       reset: vi.fn(),
  //     });

  //     renderView();
  //     await uploadTestFile(user);

  //     expect(await screen.findByText('Start over')).toBeInTheDocument();
  //     expect(screen.queryByText('Refine eCR')).not.toBeInTheDocument();
  //     expect(
  //       screen.getByText(
  //         'No conditions reportable to your jurisdiction were found in the RR.'
  //       )
  //     ).toBeInTheDocument();
  //   });
  // });
});

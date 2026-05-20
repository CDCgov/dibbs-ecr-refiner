import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Simulator } from '.';
import { MemoryRouter } from 'react-router';
import {
  useDiscoverConfigurations,
  useUploadEcr,
} from '../../api/simulator/simulator.ts';
import { Mock } from 'vitest';
import { ERROR_UPLOAD_MESSAGE } from '@components/FileUploadWarning/index.tsx';
import { uploadTestFile } from '../Configurations/ConfigTest/index.test.tsx';
import { AxiosError } from 'axios';
import { TestQueryClientProvider } from '../../test-utils.tsx';
import { DiscoveredConfigurationsResponse } from '../../api/schemas';

vi.mock('../../api/simulator/simulator', () => ({
  useUploadEcr: vi.fn(),
  useDiscoverConfigurations: vi.fn(),
}));

vi.mock('../../hooks/useGetEnv', () => ({
  useGetEnv: vi.fn(() => 'local'),
}));

const mockConfigDiscoveryResponse: DiscoveredConfigurationsResponse = {
  sets: [
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

const renderView = () =>
  render(
    <MemoryRouter>
      <TestQueryClientProvider>
        <Simulator />
      </TestQueryClientProvider>
    </MemoryRouter>
  );

type MutationParam = {
  onError?: (error: Error) => void;
};

describe('Simulate testing', () => {
  describe('Simulate testing - errors during config discovery', () => {
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
            sets: [],
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

  describe('Simulate testing - errors during refinement', () => {
    beforeEach(() => {
      (useDiscoverConfigurations as unknown as Mock).mockReturnValue({
        mutateAsync: vi.fn().mockResolvedValue({
          status: 200,
          data: mockConfigDiscoveryResponse,
        }),
        data: { data: mockConfigDiscoveryResponse },
        reset: vi.fn(),
      });

      (useUploadEcr as unknown as Mock).mockImplementation(
        ({ mutation }: { mutation?: MutationParam }) => ({
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
          data: undefined,
          reset: vi.fn(),
        })
      );
    });

    afterEach(() => {
      vi.resetAllMocks();
    });

    it('should navigate to the error view when the upload request fails', async () => {
      const user = userEvent.setup();

      renderView();
      await uploadTestFile(user);

      // configs load successfully, now trigger the refinement which will fail
      await user.click(
        await screen.findByText('Refine eCR', { selector: 'button' })
      );

      expect(await screen.findByText(ERROR_UPLOAD_MESSAGE)).toBeInTheDocument();
      expect(await screen.findByText('Server is down')).toBeInTheDocument();

      await user.click(await screen.findByText('Try again'));
      expect(
        await screen.findByText('Refine .zip file', { selector: 'button' })
      ).toBeInTheDocument();
    });
  });
});

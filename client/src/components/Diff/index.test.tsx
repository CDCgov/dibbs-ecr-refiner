import { render, screen } from '@testing-library/react';
import { Diff } from '.';
import { Condition } from '../../api/schemas';
import { TestQueryClientProvider } from '../../test-utils';

const mockMatchedCondition: Condition = {
  code: '840539006',
  display_name: 'COVID-19',
  refined_eicr: '<xml>refined covid</xml>',
  refined_rr: '<xml>refined covid</xml>',
  stats: ['eICR file reduced by 71%'],
};

vi.mock('../../api/info/info', () => {
  return {
    useGetFileUploadThresholds: vi.fn(() => ({
      data: {
        data: {
          max_mb_for_diff_rendering: 1.75,
          max_mb_for_uncompressed: 15,
        },
      },
    })),
  };
});

describe('ExternalLink', () => {
  it('should display a warning if the file size is too big', () => {
    render(
      <TestQueryClientProvider>
        <Diff
          refined_download_key=""
          unrefined_eicr=""
          condition={mockMatchedCondition}
          renderDiff={false}
        ></Diff>
      </TestQueryClientProvider>
    );
    expect(
      screen.getByText('Maximum uncompressed file size is', {
        exact: false,
      })
    ).toBeInTheDocument();
  });
});

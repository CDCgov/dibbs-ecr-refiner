import { render, screen } from '@testing-library/react';
import { Diff } from '.';
import { Condition, FileInfoResponseValue } from '../../api/schemas';

const mockMatchedCondition: Condition = {
  code: '840539006',
  display_name: 'COVID-19',
  refined_eicr: '<xml>refined covid</xml>',
  stats: ['eICR file reduced by 71%'],
  render_diff: true,
};

describe('Diff view', () => {
  it('should display a warning if the file size is too big', () => {
    render(
      <Diff
        refined_download_key=""
        unrefined_eicr=""
        condition={mockMatchedCondition}
        renderDiff={false}
      />
    );
    expect(
      screen.getByText(
        `Maximum uncompressed file size is ${FileInfoResponseValue.max_for_diff_rendering_mb}MB`
      )
    ).toBeInTheDocument();
  });
});

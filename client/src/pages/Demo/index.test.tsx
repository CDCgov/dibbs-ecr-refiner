import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  ApiUploadError,
  DemoUploadResponse,
  uploadDemoFile,
} from '../../services/demo';
import Demo from '.';
import { BrowserRouter } from 'react-router';

const mockUploadResponse: DemoUploadResponse = {
  unrefined_eicr: '<data>tons of data here</data>',
  refined_eicr: '<data>less data</data>',
};

vi.mock(import('../../services/demo.ts'), async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    uploadDemoFile: vi.fn(),
  };
});

const renderDemoView = () =>
  render(
    <BrowserRouter>
      <Demo />
    </BrowserRouter>
  );

describe('Demo', () => {
  it('should navigate through the various views in the expected order', async () => {
    const user = userEvent.setup();
    renderDemoView();

    // check that we start on the "run test" page
    const runTestPageText =
      'We will upload a test file for you to view the refinement results';
    expect(screen.getByText(runTestPageText)).toBeInTheDocument();

    // navigate to reportable conditions
    vi.mocked(uploadDemoFile).mockResolvedValue(mockUploadResponse);
    await user.click(screen.getByText('Run test'));
    expect(uploadDemoFile).toHaveBeenCalledOnce();

    // check reportable conditions view
    expect(
      screen.getByText('We found the following reportable condition(s):')
    ).toBeInTheDocument();
    await user.click(screen.getByText('Refine eCR', { selector: 'button' }));

    // check success page
    expect(screen.getByText('eCR successfully refined!')).toBeInTheDocument();
    expect(screen.getByText('tons of data here')).toBeInTheDocument();
    expect(screen.getByText('less data')).toBeInTheDocument();
  });

  it('should navigate to the error view when the upload request fails', async () => {
    const user = userEvent.setup();
    renderDemoView();

    // throw an api error when attempting to run the test
    vi.mocked(uploadDemoFile).mockRejectedValue(
      new ApiUploadError('API call failed')
    );
    await user.click(screen.getByText('Run test'));

    // check that we made it to the error view
    expect(screen.getByText('The file could not be read.')).toBeInTheDocument();

    // return to the start to try again
    await user.click(screen.getByText('Try again'));
    expect(
      screen.getByText('Run test', { selector: 'button' })
    ).toBeInTheDocument();
  });
});

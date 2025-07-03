import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  ApiUploadError,
  DemoUploadResponse,
  uploadDemoFile,
  uploadCustomZipFile,
} from '../../services/demo';
import Demo from '.';
import { BrowserRouter } from 'react-router';

// TEST: This test was originally written to test the Demo Page. This has
// been changed to `/testing` as of 2025-06-27. These tests have not been
// modified although the page has changed.

const mockUploadResponse: DemoUploadResponse = {
  conditions: [
    {
      code: 'mock-code',
      display_name: 'mock condition name',
      refined_eicr: '<data>less data</data>',
      stats: ['eICR reduced by 59%'],
    },
  ],
  unrefined_eicr: '<data>tons of data here</data>',
  refined_download_token: 'test-token',
};

const mockCustomUploadResponse: DemoUploadResponse = {
  conditions: [
    {
      code: 'mock-custom-file',
      display_name: 'custom condition',
      refined_eicr: '<data>refined custom data</data>',
      stats: ['eICR reduced by 77%'],
    },
  ],
  unrefined_eicr: '<data>unrefined custom data</data>',
  refined_download_token: 'custom-test-token',
};

vi.mock(import('../../services/demo.ts'), async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    uploadDemoFile: vi.fn(),
    uploadCustomZipFile: vi.fn(),
  };
});

const renderDemoView = () =>
  render(
    <BrowserRouter>
      <Demo />
    </BrowserRouter>
  );

describe('Demo', () => {
  it('should navigate the demo flow using the sample file', async () => {
    const user = userEvent.setup();
    renderDemoView();

    // check that we start on the "run test" page
    expect(
      screen.getByText('You can try out eCR Refiner with our test file.')
    ).toBeInTheDocument();

    // navigate to reportable conditions
    vi.mocked(uploadDemoFile).mockResolvedValue(mockUploadResponse);
    await user.click(screen.getByText('Use test file'));
    expect(uploadDemoFile).toHaveBeenCalledOnce();

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
    expect(screen.getByText('tons of data here')).toBeInTheDocument();
    expect(screen.getByText('less data')).toBeInTheDocument();
    expect(screen.getByText('eICR reduced by 59%')).toBeInTheDocument();
  });

  it('should navigate the demo flow using an uploaded zip file', async () => {
    const user = userEvent.setup();
    renderDemoView();

    // check that we start on the "run test" page
    expect(screen.getByText('Select .zip file')).toBeInTheDocument();

    const file = new File(['test'], 'test.zip', { type: 'application/zip' });
    const input: HTMLInputElement = screen.getByLabelText('Select .zip file');

    // upload the file
    vi.mocked(uploadCustomZipFile).mockResolvedValue(mockCustomUploadResponse);
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
    expect(uploadDemoFile).toHaveBeenCalledOnce();

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
    expect(screen.getByText('unrefined custom data')).toBeInTheDocument();
    expect(screen.getByText('refined custom data')).toBeInTheDocument();
    expect(screen.getByText('eICR reduced by 77%')).toBeInTheDocument();
  });

  it('should navigate to the error view when the upload request fails', async () => {
    const user = userEvent.setup();
    renderDemoView();

    // throw an api error when attempting to run the test
    vi.mocked(uploadDemoFile).mockRejectedValue(
      new ApiUploadError('API call failed')
    );
    await user.click(screen.getByText('Use test file'));

    // check that we made it to the error view
    expect(
      screen.getByText(
        'Please double check the format and size. It must be less than 10MB in size.'
      )
    ).toBeInTheDocument();

    // Server error should be shown to the user
    expect(screen.getByText('Error: API call failed')).toBeInTheDocument();

    // return to the start to try again
    await user.click(screen.getByText('Try again'));
    expect(
      screen.getByText('Use test file', { selector: 'button' })
    ).toBeInTheDocument();
  });
});

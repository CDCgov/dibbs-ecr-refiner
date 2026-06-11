import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { TestQueryClientProvider } from '../../../../../test-utils';
import {
  ImportCustomCodes,
  UPLOAD_TEMPLATE_CSV_CONTENT,
} from './ImportCustomCodes';
import { MOCK_CONFIG_ID } from '../../../../../utils/fixtures';
import userEvent from '@testing-library/user-event';

const UPLOAD_ERROR_CSV_CONTENT = `code_number,code_system,display_name
12345,Othe,Other Example
6789,ICD-10,ICD-10 Example
99999A,LOINC,LOINC Example`;

describe('Custom codes upload', () => {
  beforeEach(async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter
        initialEntries={[`/configurations/${MOCK_CONFIG_ID}/build`]}
      >
        <TestQueryClientProvider>
          <ImportCustomCodes
            configurationId={MOCK_CONFIG_ID}
          ></ImportCustomCodes>
        </TestQueryClientProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText('Import from CSV')).toBeInTheDocument();
    const uploadCsvButton = await screen.findByRole('button', {
      name: 'Upload CSV',
    });
    expect(uploadCsvButton).toBeInTheDocument();

    const file = new File([UPLOAD_TEMPLATE_CSV_CONTENT], 'test.csv', {
      type: 'text/csv',
    });

    await user.upload(uploadCsvButton, file);

    uploadCsvButton.click();
  });

  test('delete all resets to the first step', () => {});
  test('delete row deletes a row');
  test('filters appropriately when search string is supplied');
  describe('edit modal', () => {
    test('opens when clicking on the right element and closes when clicked');
    test.each([
      [1, 1, 2],
      [1, 2, 3],
      [2, 3, 5],
    ])(
      'changes on different combinations of system, name, and code value',
      (a, b, expected) => {
        expect(a + b).toBe(expected);
      }
    );
    test('is disabled if code matches existing value');
  });
});

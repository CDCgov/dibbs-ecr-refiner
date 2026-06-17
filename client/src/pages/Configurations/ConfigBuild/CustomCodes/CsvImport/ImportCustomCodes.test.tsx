import {
  MatcherFunction,
  render,
  screen,
  within,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { TestQueryClientProvider } from '../../../../../test-utils';
import {
  ImportCustomCodes,
  UPLOAD_TEMPLATE_CSV_CONTENT,
} from './ImportCustomCodes';
import { MOCK_CONFIG_ID } from '../../../../../utils/fixtures';
import userEvent from '@testing-library/user-event';
import { useUploadCustomCodesCsv } from '../../../../../api/configurations/configurations';
import { Mock } from 'vitest';

const UPLOAD_ERROR_CSV_CONTENT = `code_number,code_system,display_name
12345,Othe,Other Example
6789,ICD-10,ICD-10 Example
99999A,LOINC,LOINC Example`;

const mockUploadResponse = {
  message: 'Successfully uploaded custom codes.',

  preview_items: [
    {
      id: '15b8c6b9-d524-4519-9783-a2590494348a',
      code: '12345',
      system_key: 'other',
      name: 'Other Example',
      row: 2,
    },
    {
      id: 'e395f9f7-7c77-47ae-9e7e-2f61e9eaba98',
      code: '6789',
      system_key: 'icd10',
      name: 'ICD-10 Example',
      row: 3,
    },
    {
      id: 'c4f39082-7a57-45cd-98d8-adc3bd034568',
      code: '99999A',
      system_key: 'loinc',
      name: 'LOINC Example',
      row: 4,
    },
  ],
  codes_processed: 3,
  total_custom_codes_in_configuration: 3,
  code_systems: {
    snomed: {
      id: '5675054c-9546-4132-b804-cf86dc564ec5',
      key: 'snomed',
      display_name: 'SNOMED',
      oid: '2.16.840.1.113883.6.96',
    },
    loinc: {
      id: '0456a390-8fe8-4d89-9f6e-7bdf940a6ffe',
      key: 'loinc',
      display_name: 'LOINC',
      oid: '2.16.840.1.113883.6.1',
    },
    icd10: {
      id: 'd4ec2af7-0274-4ee5-b565-e6285d60dc84',
      key: 'icd10',
      display_name: 'ICD-10',
      oid: '2.16.840.1.113883.6.90',
    },
    rxnorm: {
      id: '69e1b668-1d40-4f30-8b9e-918484bca3bb',
      key: 'rxnorm',
      display_name: 'RxNorm',
      oid: '2.16.840.1.113883.6.88',
    },
    cvx: {
      id: '97eb3665-311d-4535-8570-67fc51914f9f',
      key: 'cvx',
      display_name: 'CVX',
      oid: '2.16.840.1.113883.12.292',
    },
    other: {
      id: '0f151a1a-fd89-40da-a267-e8dd1831b095',
      key: 'other',
      display_name: 'Other',
      oid: 'Other',
    },
  },
};

vi.mock('../../../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useUploadCustomCodesCsv: vi.fn(),
  };
});

describe('Custom codes upload', () => {
  const user = userEvent.setup();

  beforeEach(async () => {
    (useUploadCustomCodesCsv as unknown as Mock).mockReturnValue({
      mutate: vi.fn((variables, options) => {
        if (options?.onSuccess) options.onSuccess({ data: mockUploadResponse });
        if (options?.onSettled) options.onSettled({}, null, variables);
      }),
    });

    render(
      <MemoryRouter
        initialEntries={[`/configurations/${MOCK_CONFIG_ID}/build`]}
      >
        <TestQueryClientProvider>
          <ImportCustomCodes configurationId={MOCK_CONFIG_ID} />
        </TestQueryClientProvider>
      </MemoryRouter>
    );
    expect(await screen.findByText('Import from CSV')).toBeInTheDocument();
    const uploadCsvButton = screen.getByLabelText(
      'Bulk custom code upload file input'
    );
    expect(uploadCsvButton).toBeInTheDocument();

    const file = new File([UPLOAD_TEMPLATE_CSV_CONTENT], 'test.csv', {
      type: 'text/csv',
    });

    await user.upload(uploadCsvButton, file);

    uploadCsvButton.click();
    const rowsUploaded = screen.getAllByRole('row');
    expect(rowsUploaded.length).toBe(4); // 3 codes plus the header
  });

  test('delete all resets to the first step', async () => {
    await userEvent.click(screen.getByText('Undo & delete codes'));

    expect(
      screen.getByRole('heading', { name: 'Undo & delete codes' })
    ).toBeInTheDocument();
    const confirmationCopy = screen.getByText(
      'Are you sure you want to delete all these uploaded codes?',
      { exact: false }
    );
    expect(confirmationCopy).toBeInTheDocument();

    const confirmDeleteButton = screen.getByRole('button', {
      name: 'Undo & delete codes',
    });
    expect(confirmDeleteButton).toBeInTheDocument();
    await userEvent.click(confirmDeleteButton);
    expect(confirmationCopy).not.toBeInTheDocument();
  });

  test('delete row successfully deletes a row', async () => {
    const deleteRows = screen.getAllByRole('row');
    checkOtherCode();
    await userEvent.click(
      await within(deleteRows[1]).findByRole('button', { name: 'Delete' })
    );
    expect(screen.getAllByRole('row').length).toBe(3); // now 2 codes plus the header
    checkOtherCode({ exists: false });
  });
  test('filters appropriately when search string is supplied', async () => {
    const searchInput = screen.getByPlaceholderText('Search codes');
    checkOtherCode();
    checkICD10Code();
    checkLoincCode();
    // by display
    await userEvent.type(searchInput, 'Other Example');
    checkOtherCode();
    checkICD10Code({ exists: false });
    checkLoincCode({ exists: false });

    // by system
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, 'ICD-1');
    checkICD10Code();
    checkOtherCode({ exists: false });
    checkLoincCode({ exists: false });

    // by code
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, '99999A');
    checkLoincCode();
    checkICD10Code({ exists: false });
    checkOtherCode({ exists: false });
  });
});

function checkOtherCode({ exists = true } = {}) {
  const matcher = exists ? 'getByText' : 'queryByText';

  const totalExpectation = (text: string) => {
    const assertion = expect(screen[matcher](text));
    return exists
      ? assertion.toBeInTheDocument()
      : assertion.not.toBeInTheDocument();
  };

  totalExpectation('12345');
  totalExpectation('Other');
}

function checkICD10Code({ exists = true } = {}) {
  const matcher = exists ? 'getByText' : 'queryByText';

  const totalExpectation = (text: string) => {
    const assertion = expect(screen[matcher](text));
    return exists
      ? assertion.toBeInTheDocument()
      : assertion.not.toBeInTheDocument();
  };

  totalExpectation('6789');
  totalExpectation('ICD-10');
}

function checkLoincCode({ exists = true } = {}) {
  const matcher = exists ? 'getByText' : 'queryByText';

  const totalExpectation = (text: string) => {
    const assertion = expect(screen[matcher](text));
    return exists
      ? assertion.toBeInTheDocument()
      : assertion.not.toBeInTheDocument();
  };

  totalExpectation('99999A');
  totalExpectation('LOINC');
}

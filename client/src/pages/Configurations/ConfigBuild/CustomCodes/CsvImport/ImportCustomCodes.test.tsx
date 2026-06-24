import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { TestQueryClientProvider } from '../../../../../test-utils';
import { ImportCustomCodes } from './ImportCustomCodes';
import {
  MOCK_CONFIG_ID,
  mockCodeSystems,
  mockIndexedSystem,
} from '../../../../../utils/fixtures';
import userEvent from '@testing-library/user-event';
import { useUploadCustomCodesCsv } from '../../../../../api/configurations/configurations';
import { Mock } from 'vitest';

vi.mock('../../../../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../../../../api/configurations/configurations'
  );
  return {
    ...actual,
    useUploadCustomCodesCsv: vi.fn(),
  };
});

vi.mock('../../../../../api/code-systems/code-systems', async () => {
  const actual = await vi.importActual(
    '../../../../../api/code-systems/code-systems'
  );
  return {
    ...actual,
    useGetCodeSystems: vi.fn(() => ({
      data: {
        data: mockCodeSystems,
      },
    })),
  };
});

const MOCK_LOINC_CODE = '52747';
const MOCK_CVX_CODE = '23779';
const MOCK_OTHER_CODE_SUFFIX = '1534';
const MOCK_OTHER_CODE = MOCK_CVX_CODE + MOCK_OTHER_CODE_SUFFIX; // used to test prefix matching

const MOCK_UPLOAD_CSV = `code,code_system,display_name
15613,snomed,SNOMED Example
${MOCK_LOINC_CODE},loinc,LOINC Example
287972,icd10,ICD-10 Example
5128,rxnorm,RxNorm Example
${MOCK_CVX_CODE},cvx,CVX Example
${MOCK_OTHER_CODE},other,Other Example`;

vi.mock('./utils', () => {
  return {
    buildCsvDownloadTemplate: vi.fn(() => {
      return MOCK_UPLOAD_CSV;
    }),
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

    const file = new File([MOCK_UPLOAD_CSV], 'test.csv', {
      type: 'text/csv',
    });

    await user.upload(uploadCsvButton, file);

    uploadCsvButton.click();
    const rowsUploaded = screen.getAllByRole('row');
    expect(rowsUploaded.length).toBe(mockCodeSystems.length + 1); // one per system plus the header
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
    expect(screen.getAllByRole('row').length).toBe(mockCodeSystems.length);
    checkOtherCode();
  });

  test('filters appropriately when search string is supplied', async () => {
    const searchInput = screen.getByPlaceholderText('Search codes');
    checkOtherCode();
    checkIcd10Code();
    checkLoincCode();
    checkSnomedCode();
    checkCvxCode();

    // by display
    await userEvent.type(searchInput, 'SNOMED Example');
    checkSnomedCode();
    checkOtherCode(false);
    checkIcd10Code(false);
    checkLoincCode(false);
    checkCvxCode(false);

    // by system
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, 'ICD-1');
    checkIcd10Code();
    checkOtherCode(false);
    checkLoincCode(false);
    checkSnomedCode(false);
    checkCvxCode(false);

    // by code
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, MOCK_LOINC_CODE);
    checkLoincCode();
    checkOtherCode(false);
    checkIcd10Code(false);
    checkSnomedCode(false);
    checkCvxCode(false);

    // make sure codes with matching prefixes get appropriately filtered
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, MOCK_CVX_CODE);
    expect(screen.getAllByText(MOCK_CVX_CODE).length).toBe(2);
    checkLoincCode(false);
    checkSnomedCode(false);
    checkIcd10Code(false);

    await userEvent.type(searchInput, MOCK_OTHER_CODE_SUFFIX);
    checkOtherCode();
    checkCvxCode(false);
    checkLoincCode(false);
    checkSnomedCode(false);
    checkIcd10Code(false);
  });
});

function checkLoincCode(exists = true) {
  checkCode('LOINC', exists);
}

function checkSnomedCode(exists = true) {
  checkCode('SNOMED', exists);
}

function checkCvxCode(exists = true) {
  checkCode('CVX', exists);
}

function checkIcd10Code(exists = true) {
  checkCode('ICD-10', exists);
}

function checkOtherCode(exists = true) {
  checkCode('Other', exists);
}

function checkCode(codeSystemName: string, exists = true) {
  const codeSystem = mockCodeSystems.find(
    (s) => s.display_name === codeSystemName
  );

  const mockCode = mockPreviewItems.find(
    (i) => i.system_key === codeSystem?.key
  )?.code as string;

  const matcher = exists ? 'getByText' : 'queryByText';

  const totalExpectation = (text: string) => {
    const assertion = expect(screen[matcher](text));
    return exists
      ? assertion.toBeInTheDocument()
      : assertion.not.toBeInTheDocument();
  };

  totalExpectation(mockCode);
  totalExpectation(codeSystemName);
}

const uploadLines = csvToDict(MOCK_UPLOAD_CSV);

const mockPreviewItems = uploadLines.map((row, i) => {
  return {
    id: crypto.randomUUID(),
    code: row['code'],
    system_key: row['code_system'],
    name: row['display_name'],
    row: i,
  };
});

const mockUploadResponse = {
  message: 'Successfully uploaded custom codes.',
  preview_items: mockPreviewItems,
  codes_processed: mockPreviewItems.length,
  total_custom_codes_in_configuration: mockPreviewItems.length,
  code_systems: mockIndexedSystem,
};

function csvToDict(csv: string) {
  const lines = csv.trim().split('\n');
  const headers = lines[0].split(',').map((h) => h.trim());
  const indexedValues: Record<string, string>[] = [];

  lines.slice(1).forEach((line) => {
    const rowObject: Record<string, string> = {};
    const values = line.split(',');

    headers.forEach((_, j) => {
      rowObject[headers[j]] = values[j];
    });
    indexedValues.push(rowObject);
  });

  return indexedValues;
}

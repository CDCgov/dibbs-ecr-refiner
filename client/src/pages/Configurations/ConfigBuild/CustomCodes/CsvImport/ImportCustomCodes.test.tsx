import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { TestQueryClientProvider } from '../../../../../test-utils';
import { ImportCustomCodes } from './ImportCustomCodes';
import userEvent from '@testing-library/user-event';
import { useUploadCustomCodesCsv } from '../../../../../api/configurations/configurations';
import { Mock } from 'vitest';
import {
  DbCodeSystem,
  IndexedCodeSystem,
  UploadCustomCodesPreviewItem,
  UploadCustomCodesPreviewResponse,
} from '../../../../../api/schemas';

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
const MOCK_SNOMED_CODE = '15613';
const MOCK_CVX_CODE = '23779';

const MOCK_OTHER_CODE_SUFFIX = '1534';
const MOCK_OTHER_CODE = MOCK_CVX_CODE + MOCK_OTHER_CODE_SUFFIX; // used to test prefix matching

const MOCK_UPLOAD_CSV = `code,code_system,display_name
${MOCK_SNOMED_CODE},snomed,SNOMED Example
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

async function renderAndUploadCsv(user: ReturnType<typeof userEvent.setup>) {
  render(
    <MemoryRouter initialEntries={[`/configurations/${MOCK_CONFIG_ID}/build`]}>
      <TestQueryClientProvider>
        <ImportCustomCodes configurationId={MOCK_CONFIG_ID} />
      </TestQueryClientProvider>
    </MemoryRouter>
  );

  const fileInput = screen.getByTestId('bulk-upload-file-input');
  const file = new File([MOCK_UPLOAD_CSV], 'test.csv', {
    type: 'text/csv',
  });

  await user.upload(fileInput, file);
}
beforeEach(() => {
  (useUploadCustomCodesCsv as unknown as Mock).mockReturnValue({
    mutate: vi.fn((variables, options) => {
      if (options?.onSuccess) options.onSuccess({ data: mockUploadResponse });
      if (options?.onSettled) options.onSettled({}, null, variables);
    }),
  });
});

describe('Custom codes upload', () => {
  test('delete all resets to the first step', async () => {
    const user = userEvent.setup();
    await renderAndUploadCsv(user);
    await user.click(screen.getByText('Undo & delete codes'));

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
    const user = userEvent.setup();
    await renderAndUploadCsv(user);
    const deleteRows = screen.getAllByRole('row');
    checkAllCodesExistence();

    await userEvent.click(
      await within(deleteRows[0]).findByRole('button', { name: 'Delete' })
    );
    expect(screen.getAllByRole('row').length).toBe(mockCodeSystems.length - 1);

    checkSnomedCode(false); // first row is the SNOMED row
    checkOtherCode();
    checkIcd10Code();
    checkLoincCode();
    checkRxNormCode();
    checkCvxCode();
  });

  test('filters appropriately when search string is supplied', async () => {
    const user = userEvent.setup();
    await renderAndUploadCsv(user);

    const searchInput = screen.getByPlaceholderText('Search codes');
    checkAllCodesExistence();
    // by display
    await userEvent.type(searchInput, 'LOINC Example');
    checkLoincCode();
    checkSnomedCode(false);
    checkOtherCode(false);
    checkRxNormCode(false);
    checkIcd10Code(false);
    checkCvxCode(false);

    // by code
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, MOCK_LOINC_CODE);
    checkLoincCode();
    checkOtherCode(false);
    checkIcd10Code(false);
    checkRxNormCode(false);
    checkSnomedCode(false);
    checkCvxCode(false);

    // make sure codes with matching prefixes get appropriately filtered
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, MOCK_CVX_CODE);
    expect(screen.getAllByText(MOCK_CVX_CODE).length).toBe(2);

    expect(screen.getByText('Other Example')).toBeInTheDocument();
    expect(screen.getByText('CVX Example')).toBeInTheDocument();
    checkLoincCode(false);
    checkSnomedCode(false);
    checkIcd10Code(false);

    await userEvent.type(searchInput, MOCK_OTHER_CODE_SUFFIX);
    checkOtherCode();
    checkCvxCode(false);
    checkLoincCode(false);
    checkRxNormCode(false);
    checkSnomedCode(false);
    checkIcd10Code(false);
  });

  describe('edit modal', () => {
    test('opens when clicked', async () => {
      const user = userEvent.setup();
      await renderAndUploadCsv(user);

      const editRows = screen.getAllByRole('row');
      checkAllCodesExistence();

      await user.click(
        await within(editRows[0]).findByRole('button', { name: 'Edit' })
      );

      expect(screen.getByText(`Edit ${MOCK_SNOMED_CODE}`)).toBeInTheDocument();
    });

    test('disables save state when any one of the three required fields is missing', async () => {
      const user = userEvent.setup();
      await renderAndUploadCsv(user);
      const editRows = screen.getAllByRole('row');

      await user.click(
        await within(editRows[0]).findByRole('button', { name: 'Edit' })
      );

      const saveButton = screen.getByRole('button', { name: 'Save changes' });
      expect(saveButton).toBeEnabled();

      const code = screen.getByLabelText('Code');
      await user.clear(code);
      expect(saveButton).toBeDisabled();

      await user.type(code, '13535135');
      const codeName = screen.getByLabelText('Code name');

      await user.clear(codeName);
      expect(saveButton).toBeDisabled();

      await user.type(codeName, 'SNOMED Example');
      expect(saveButton).toBeEnabled();
    });
  });
});

function checkAllCodesExistence() {
  checkSnomedCode();
  checkOtherCode();
  checkIcd10Code();
  checkLoincCode();
  checkLoincCode();
  checkCvxCode();
}

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
function checkRxNormCode(exists = true) {
  checkCode('RxNorm', exists);
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
  totalExpectation(`${codeSystemName} Example`);
}

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

export const mockCodeSystems: DbCodeSystem[] = [
  {
    id: '157a00b0-62e6-48c8-b822-475c5d855f3f',
    key: 'snomed',
    display_name: 'SNOMED',
    oid: '2.16.840.1.113883.6.96',
  },
  {
    id: 'bd5ad8fd-f94c-4fcf-97ee-5b63c2e7a42b',
    oid: '2.16.840.1.113883.6.1',
    key: 'loinc',
    display_name: 'LOINC',
  },
  {
    id: '375d4fd5-81f8-4b9e-abd9-979c7987691f',
    oid: '2.16.840.1.113883.6.90',
    key: 'icd10',
    display_name: 'ICD-10',
  },
  {
    id: 'c645801a-26f2-495c-b07f-e9be5ac26275',
    oid: '2.16.840.1.113883.6.88',
    key: 'rxnorm',
    display_name: 'RxNorm',
  },
  {
    id: '4306c91c-a8e2-4f4b-b673-0da9a6432b38',
    oid: '2.16.840.1.113883.12.292',
    key: 'cvx',
    display_name: 'CVX',
  },
  {
    id: 'f65063a3-6836-41ce-8ab8-253994907faa',
    oid: 'Other',
    key: 'other',
    display_name: 'Other',
  },
];

export const mockIndexedSystem: IndexedCodeSystem = mockCodeSystems.reduce(
  (acc: Record<string, DbCodeSystem>, curCodeSystem) => {
    acc[curCodeSystem.key] = curCodeSystem;
    return acc;
  },
  {}
);

export const MOCK_CONFIG_ID = 'd8cf3930-a7c2-4761-9ba9-ce72ff9191c8';

const uploadLines = csvToDict(MOCK_UPLOAD_CSV);
const mockPreviewItems: UploadCustomCodesPreviewItem[] = uploadLines.map(
  (row, i) => {
    return {
      id: crypto.randomUUID(),
      code: row['code'],
      system_key: row['code_system'],
      name: row['display_name'],
      row: i,
    };
  }
);

const mockUploadResponse: UploadCustomCodesPreviewResponse = {
  preview_items: mockPreviewItems,
  codes_processed: mockPreviewItems.length,
  total_custom_codes_in_configuration: mockPreviewItems.length,
  code_systems: mockIndexedSystem,
};

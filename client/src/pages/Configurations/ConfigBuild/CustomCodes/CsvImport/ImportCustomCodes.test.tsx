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
import {
  CSV_DOWNLOAD_TEMPLATE,
  EXAMPLE_CVX_CODE,
  EXAMPLE_LOINC_CODE,
  EXAMPLE_OTHER_CODE_SUFFIX,
  EXAMPLE_SNOMED_CODE,
} from './utils';
import {
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

async function renderAndUploadCsv(user: ReturnType<typeof userEvent.setup>) {
  render(
    <MemoryRouter initialEntries={[`/configurations/${MOCK_CONFIG_ID}/build`]}>
      <TestQueryClientProvider>
        <ImportCustomCodes configurationId={MOCK_CONFIG_ID} />
      </TestQueryClientProvider>
    </MemoryRouter>
  );

  const fileInput = screen.getByLabelText('Bulk custom code upload file input');
  const file = new File([CSV_DOWNLOAD_TEMPLATE], 'test.csv', {
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
    checkIcd10Code(false);
    checkCvxCode(false);

    // by code
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, EXAMPLE_LOINC_CODE);
    checkLoincCode();
    checkOtherCode(false);
    checkIcd10Code(false);
    checkSnomedCode(false);
    checkCvxCode(false);

    // make sure codes with matching prefixes get appropriately filtered
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, EXAMPLE_CVX_CODE);
    expect(screen.getAllByText(EXAMPLE_CVX_CODE).length).toBe(2);

    expect(screen.getByText('Other Example')).toBeInTheDocument();
    expect(screen.getByText('CVX Example')).toBeInTheDocument();
    checkLoincCode(false);
    checkSnomedCode(false);
    checkIcd10Code(false);

    await userEvent.type(searchInput, EXAMPLE_OTHER_CODE_SUFFIX);
    checkOtherCode();
    checkCvxCode(false);
    checkLoincCode(false);
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

      expect(
        screen.getByText(`Edit ${EXAMPLE_SNOMED_CODE}`)
      ).toBeInTheDocument();
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
  const mockCode = mockPreviewItems.find((i) => i.system_key === codeSystemName)
    ?.code as string;

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

const uploadLines = csvToDict(CSV_DOWNLOAD_TEMPLATE);
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

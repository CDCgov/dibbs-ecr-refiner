import { useQueryClient } from '@tanstack/react-query';
import React, { useRef, useState, useEffect } from 'react';
import {
  useUploadCustomCodesCsv,
  useConfirmUploadCustomCodesCsv,
  getGetConfigurationQueryKey,
} from '../../../../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../../../../hooks/useErrorFormatter';
import { useSearch } from '../../../../../hooks/useSearch';
import { useToast } from '../../../../../hooks/useToast';
import { highlightMatches } from '../../../../../utils';
import { ConfirmModal, UndoModal, PreviewEditModal } from './Modals';
import { Button } from '@components/Button';
import { CsvImportStep } from '../..';
import { Search } from '@components/Search';
import {
  IndexedCodeSystem,
  UploadCustomCodesPreviewItem,
} from '../../../../../api/schemas';
import { useGetCodeSystems } from '../../../../../api/code-systems/code-systems';
import { buildCsvDownloadTemplate } from './utils';
import { FuseResult } from 'fuse.js';
import { UploadIcon } from '@components/Icons/UploadIcon';

interface UploadCsvError {
  response?: {
    data?: {
      detail?: {
        errors?: Array<{
          row?: number | string;
          error?: string;
        }>;
      };
    };
  };
}

interface RowError {
  row: number;
  error: string;
}
export interface UploadError {
  message: string;
  rowErrors?: RowError[];
}

type OpenModalState = 'confirm' | 'undo' | 'none';

interface ImportCustomCodesProps {
  configurationId: string;
  disabled?: boolean;
  onSuccess?: () => void;
  onStepChange?: (step: CsvImportStep) => void;
}
export function ImportCustomCodes({
  configurationId,
  disabled = false,
  onSuccess,
  onStepChange,
}: ImportCustomCodesProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const showToast = useToast();
  const formatApiError = useApiErrorFormatter();
  const { mutate: uploadCsvMutation, isPending: isUploadPending } =
    useUploadCustomCodesCsv();
  const { mutate: confirmCsvMutation, isPending: isConfirming } =
    useConfirmUploadCustomCodesCsv();

  const [previewItems, setPreviewItems] = useState<
    UploadCustomCodesPreviewItem[]
  >([]);
  const [codeSystems, setCodeSystems] = useState<IndexedCodeSystem | null>(
    null
  );

  const [error, setError] = useState<UploadError | null>(null);
  const [step, setStep] = useState<CsvImportStep>('intro');
  const [curOpenModal, setCurOpenModal] = useState<OpenModalState>('none');
  const [isUploading, setIsUploading] = useState(false);

  const {
    searchText,
    setSearchText,
    results: previewSearchResults,
  } = useSearch(previewItems, {
    keys: [
      { name: 'code', weight: 0.6 },
      { name: 'name', weight: 0.4 },
    ],
    includeMatches: true,
    threshold: 0.3,
  });
  useEffect(() => {
    onStepChange?.(step);

    if (step === 'preview') {
      setSearchText('');
    }
  }, [step, onStepChange, setSearchText]);

  const exitPreviewStep = (resetStep: boolean) => {
    setPreviewItems([]);
    setError(null);
    onSuccess?.();
    if (resetStep) {
      setStep('intro');
    }
  };

  const handleFileUpload = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) {
      setError({ message: 'Please upload a file.' });
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError({ message: 'Please upload a valid CSV file.' });
      return;
    }

    setError(null);
    setIsUploading(true);

    const csvText = await file.text();

    uploadCsvMutation(
      {
        configurationId,
        data: {
          csv_text: csvText,
          filename: file.name,
        },
      },
      {
        onSuccess: (res) => {
          setError(null);

          const previewItems = res.data.preview_items;
          const codeSystems = res.data.code_systems;

          setCodeSystems(codeSystems);
          setPreviewItems(previewItems);
          setStep('preview');
        },
        onError: (err: unknown) => {
          const csvError = err as UploadCsvError;
          const parsedErrors = csvError.response?.data?.detail?.errors;

          if (!parsedErrors) {
            const message = formatApiError(err);
            setError({ message: message });
            showToast({
              variant: 'error',
              heading: 'Error uploading CSV',
              body: message,
            });
            return;
          }

          const parsed = parsedErrors.map(({ row, error }) => ({
            row: Number(row),
            error: String(error),
          }));
          setError({ message: 'Error importing CSV', rowErrors: parsed });
          setStep('error');
          showToast({
            variant: 'error',
            heading: 'Error importing CSV',
            body: `${parsed.length} errors`,
          });
        },
        onSettled: () => {
          setIsUploading(false);
        },
      }
    );
  };

  const handleConfirm = () => {
    if (!previewItems?.length) return;

    setCurOpenModal('none');
    confirmCsvMutation(
      {
        configurationId,
        data: {
          custom_codes: previewItems,
        },
      },
      {
        onSuccess: async (res) => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          showToast({
            heading: 'CSV confirmed',
            body: `${res.data.codes_processed ?? previewItems.length} codes imported.`,
          });
          handleDelete(false);
        },
        onError: (err: unknown) => {
          const message = formatApiError(err);
          showToast({
            variant: 'error',
            heading: 'Error confirming CSV',
            body: message,
          });
          handleDelete();
        },
      }
    );
  };

  const handleDelete = (resetStep = false) => {
    exitPreviewStep(resetStep);
  };

  const handleBack = () => {
    if (isUploading || isUploadPending) {
      setIsUploading(false);
      return;
    }

    if (step === 'preview') {
      handleDelete(false);
      return;
    }

    onSuccess?.();
  };

  const previewDisplayItems = searchText
    ? previewSearchResults
    : previewItems.map((i) => {
        return { item: i, matches: [], refIndex: -1 };
      });

  return (
    <>
      <div className="w-full space-y-6">
        <>
          <Button
            variant="tertiary"
            onClick={handleBack}
            className="text-blue-cool-50 text-sm hover:underline"
          >
            ← Back
          </Button>
          <h2 className="m-0 py-4 text-2xl font-semibold">Import from CSV</h2>
          <p className="text-sm text-gray-600">
            Easily add multiple codes by uploading a spreadsheet in CSV format.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept=".csv"
            data-testid="bulk-upload-file-input"
            onChange={handleFileChange}
          />
        </>
        {isUploading || isUploadPending ? (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-8 text-center">
            <div className="mb-4 flex justify-center">
              <UploadIcon />
            </div>

            <h3 className="mb-4 text-lg font-semibold">CSV uploading...</h3>

            <div className="mx-auto mb-6 h-1 w-3/4 overflow-hidden rounded bg-blue-200">
              <div className="h-full w-1/3 animate-pulse bg-blue-600" />
            </div>

            <Button
              variant="secondary"
              onClick={() => setIsUploading(false)}
              disabled={isUploadPending}
            >
              Cancel
            </Button>
          </div>
        ) : step === 'intro' ? (
          <div className="w-full max-w-xl space-y-6">
            <UploadInstructions
              handleButtonClick={handleFileUpload}
              disabled={disabled}
              codeSystems={codeSystems}
            />
            {error && (
              <div role="alert" className="text-sm text-red-600">
                {error.message}
              </div>
            )}
          </div>
        ) : step === 'error' ? (
          <div className="flex flex-col gap-6">
            <p className="font-bold">
              Please fix the errors in your CSV and re-upload it.
            </p>
            <Button
              onClick={handleFileUpload}
              disabled={disabled}
              variant="primary"
              className="max-w-40 px-5"
            >
              Re-upload CSV
            </Button>
            <div className="mb-2">
              {error && (
                <p role="alert" className="text-sm text-red-700">
                  {error.message}
                </p>
              )}
            </div>
            {error?.rowErrors && error?.rowErrors.length > 0 ? (
              <>
                <hr className="border-gray-cool-20" />
                <table className="w-full border-spacing-y-2 text-left text-sm">
                  <tbody>
                    {error.rowErrors.map(({ row, error }) => (
                      <tr key={`${row}-${error}`} className="h-6 text-red-700">
                        <td className="w-20 px-3 py-3 font-bold">
                          Row {row > 0 ? row : '—'}
                        </td>
                        <td className="px-3 py-3">{error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            ) : (
              <p className="text-sm text-red-700">
                Try uploading the file again or download a fresh template.
              </p>
            )}
          </div>
        ) : step === 'preview' && previewItems ? (
          <div className="flex flex-col gap-6">
            <p className="text-sm font-bold text-gray-600">
              Review the codes below to make sure they are correct
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                onClick={() => setCurOpenModal('confirm')}
                disabled={isConfirming}
              >
                Confirm & save codes
              </Button>
              <Button
                variant="tertiary"
                onClick={() => setCurOpenModal('undo')}
              >
                Undo & delete codes
              </Button>
            </div>
            <hr className="border-gray-cool-20" />
            <div className="mb-2 flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-2">
                <Search
                  placeholder="Search codes"
                  value={searchText}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                    setSearchText(event.target.value)
                  }
                  id="csv-preview-search"
                  name="csv-preview-search"
                  className="w-full min-w-60"
                />
              </div>
            </div>

            <PreviewEditTable
              previewDisplayItems={previewDisplayItems}
              setPreviewItems={setPreviewItems}
              codeSystems={codeSystems}
              exitPreviewStep={() => setStep('intro')}
              error={error}
              setError={setError}
            />

            {error && (
              <div role="alert" className="text-sm text-red-600">
                {error.message}
              </div>
            )}
          </div>
        ) : null}
      </div>

      <ConfirmModal
        isOpen={curOpenModal === 'confirm'}
        onClose={() => setCurOpenModal('none')}
        handleConfirm={handleConfirm}
      />

      <UndoModal
        isOpen={curOpenModal === 'undo'}
        onClose={() => setCurOpenModal('none')}
        handleDelete={() => handleDelete(true)}
      />
    </>
  );
}

interface PreviewEditTableProps {
  previewDisplayItems: FuseResult<UploadCustomCodesPreviewItem>[];
  setPreviewItems: React.Dispatch<
    React.SetStateAction<UploadCustomCodesPreviewItem[]>
  >;
  codeSystems: IndexedCodeSystem | null;
  error: UploadError | null;
  exitPreviewStep: () => void;
  setError: React.Dispatch<React.SetStateAction<UploadError | null>>;
}
function PreviewEditTable({
  previewDisplayItems,
  setPreviewItems,
  codeSystems,
  error,
  setError,
  exitPreviewStep,
}: PreviewEditTableProps) {
  const [itemBeingEdited, setItemBeingEdited] =
    useState<UploadCustomCodesPreviewItem | null>(null);
  const showToast = useToast();

  const openPreviewEditModal = (editIndex: string) => {
    const target = previewDisplayItems.find((i) => i.item.id === editIndex);
    if (target) setItemBeingEdited({ ...target.item });
  };

  const closePreviewEditModal = () => {
    setItemBeingEdited(null);
  };

  const handleRowDelete = (itemToDelete: UploadCustomCodesPreviewItem) => {
    setPreviewItems((prev) => {
      const updated = prev.filter((i) => i.id !== itemToDelete.id);
      if (updated.length === 0) {
        exitPreviewStep();
      }
      return updated;
    });
    showToast({
      heading: 'Row deleted',
      body: itemToDelete.code,
    });
  };

  const isPreviewEditModalOpen = itemBeingEdited !== null;

  return (
    <>
      <table className="w-full border-separate border-spacing-y-2 text-left text-sm">
        <thead className="sr-only">
          <tr>
            <th>Custom code</th>
            <th>Custom code system</th>
            <th>Custom code name</th>
            <th>Modify the custom code</th>
          </tr>
        </thead>

        <tbody>
          {codeSystems &&
            previewDisplayItems.map((previewItem) => (
              <PreviewRow
                previewItem={previewItem}
                codeSystems={codeSystems}
                openPreviewEditModal={openPreviewEditModal}
                handleRowDelete={handleRowDelete}
                key={previewItem.item.id}
              />
            ))}
        </tbody>
      </table>
      {codeSystems && itemBeingEdited && (
        <PreviewEditModal
          previewEditItem={itemBeingEdited}
          setPreviewItems={setPreviewItems}
          closePreviewEditModal={closePreviewEditModal}
          previewItems={previewDisplayItems.map((i) => i.item)}
          setError={setError}
          error={error}
          isOpen={isPreviewEditModalOpen}
          codeSystems={codeSystems}
        />
      )}
    </>
  );
}

interface PreviewRowProps {
  previewItem: FuseResult<UploadCustomCodesPreviewItem>;
  codeSystems: IndexedCodeSystem;
  openPreviewEditModal: (itemId: string) => void;
  handleRowDelete: (itemToDelete: UploadCustomCodesPreviewItem) => void;
}
function PreviewRow({
  previewItem,
  codeSystems,
  openPreviewEditModal,
  handleRowDelete,
}: PreviewRowProps) {
  const { item, matches } = previewItem;

  return (
    <tr className="border-y border-blue-50">
      <td className="px-2 py-1">
        {highlightMatches(item.code, matches, 'code')}
      </td>
      <td className="px-2 py-1">{codeSystems[item.system_key].display_name}</td>
      <td className="px-2 py-1">
        {highlightMatches(item.name, matches, 'name')}
      </td>
      <td className="px-2 py-1 text-right text-sm">
        <Button
          variant="tertiary"
          onClick={() => openPreviewEditModal(item.id)}
        >
          Edit
        </Button>
        <span className="px-2 text-gray-400">&nbsp;</span>
        <Button variant="tertiary" onClick={() => handleRowDelete(item)}>
          Delete
        </Button>
      </td>
    </tr>
  );
}

interface UploadInstructionProps {
  handleButtonClick: () => void;
  disabled: boolean;
  codeSystems: IndexedCodeSystem | null;
}

function UploadInstructions({
  handleButtonClick,
  disabled,
}: UploadInstructionProps) {
  const { data: codeSystems } = useGetCodeSystems();

  const downloadTemplate = () => {
    const uploadTemplateCsvContent = codeSystems?.data
      ? buildCsvDownloadTemplate(Object.values(codeSystems.data))
      : null;

    if (!uploadTemplateCsvContent) return;
    const blob = new Blob([uploadTemplateCsvContent], {
      type: 'text/csv;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'custom_code_upload_template.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);
  };
  return (
    <>
      <div className="flex items-start gap-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-400 text-sm font-medium">
          1
        </div>
        <div className="space-y-2">
          <p className="text-sm">
            Your spreadsheet must follow the format of this template.
          </p>

          <Button
            variant="secondary"
            type="button"
            onClick={downloadTemplate}
            disabled={!codeSystems}
          >
            Download template
          </Button>
        </div>
      </div>

      <div className="flex items-start gap-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-400 text-sm font-medium">
          2
        </div>
        <div className="space-y-2">
          <p className="text-sm">
            Once you have your codes in the right format, upload the CSV.
            <br />
            We will validate the codes and let you know if you need to change
            anything.
          </p>

          <Button
            type="button"
            onClick={handleButtonClick}
            disabled={disabled}
            variant="primary"
          >
            Upload CSV
          </Button>
        </div>
      </div>
    </>
  );
}

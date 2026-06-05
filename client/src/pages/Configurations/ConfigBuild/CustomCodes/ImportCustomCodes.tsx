import { useQueryClient } from '@tanstack/react-query';
import { FuseResultMatch } from 'fuse.js';
import { useRef, useState, useEffect, ChangeEvent } from 'react';
import {
  useUploadCustomCodesCsv,
  useConfirmUploadCustomCodesCsv,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import { UploadCustomCodesPreviewItem } from '../../../../api/schemas/uploadCustomCodesPreviewItem';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { useSearch } from '../../../../hooks/useSearch';
import { useToast } from '../../../../hooks/useToast';
import { highlightMatches } from '../../../../utils';
import {
  ConfirmModal,
  UndoModal,
  PreviewEditModal,
} from '../CsvCodeUploadModal';
import { Button } from '@components/Button';
import { CsvImportStep } from '../';
import UploadSvg from '../../../../assets/upload.svg';
import { Search } from '@components/Search';

const EMPTY_PREVIEW_ITEM: UploadCustomCodesPreviewItem = {
  code: '',
  system_key: 'other',
  system_display_name: 'Other',
  name: '',
};

const UPLOAD_TEMPLATE_CSV_CONTENT = `code_number,code_system,display_name
12345,Other,Other Example
6789,ICD-10,ICD-10 Example
99999A,LOINC,LOINC Example`;

type UploadCsvError = {
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
};

type RowError = { row: number; error: string };

type OpenModalType = 'confirm' | 'undo' | 'preview' | 'none';

type ImportCustomCodesProps = {
  configurationId: string;
  disabled?: boolean;
  onSuccess?: () => void;
  onStepChange?: (step: CsvImportStep) => void;
};
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

  const [error, setError] = useState<string | null>(null);
  const [uploadRowErrors, setUploadRowErrors] = useState<RowError[] | null>(
    null
  );
  const [previewItems, setPreviewItems] = useState<
    UploadCustomCodesPreviewItem[]
  >([]);

  const [step, setStep] = useState<CsvImportStep>('intro');
  const [isUploading, setIsUploading] = useState(false);
  const [previewEditIndex, setPreviewEditIndex] = useState<number | null>(null);
  const [previewEditForm, setPreviewEditForm] =
    useState<UploadCustomCodesPreviewItem>(EMPTY_PREVIEW_ITEM);
  const [curOpenModal, setCurModalOpen] = useState<OpenModalType>('none');

  useEffect(() => {
    onStepChange?.(step);
  }, [step, onStepChange]);

  useEffect(() => {
    if (step !== 'preview') return;
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [step]);

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
      setError('Please upload a file.');
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a valid CSV file.');
      setUploadRowErrors(null);
      return;
    }

    setError(null);
    setUploadRowErrors(null);
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
          setUploadRowErrors(null);

          const previewItems = res.data.preview_items;
          setPreviewItems(previewItems);
          setStep('preview');
        },
        onError: (err: unknown) => {
          const csvError = err as UploadCsvError;
          const parsedErrors = csvError.response?.data?.detail?.errors;

          if (!parsedErrors) {
            const message = formatApiError(err);
            setError(message);
            setUploadRowErrors(null);
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
          setUploadRowErrors(parsed);
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

    setCurModalOpen('none');
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
          handleDelete({ resetStep: false });
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

  const handleDelete = ({ resetStep = true }: { resetStep?: boolean } = {}) => {
    setPreviewItems([]);
    setUploadRowErrors(null);
    setError(null);
    if (resetStep) {
      setStep('intro');
    }
    onSuccess?.();
  };

  const handleBack = () => {
    if (uploading) {
      setIsUploading(false);
      return;
    }

    if (step === 'preview') {
      handleDelete({ resetStep: false });
      return;
    }

    onSuccess?.();
  };

  const openPreviewEditModal = (previewIndex: number) => {
    const target = previewItems?.[previewIndex];
    if (!target) return;
    setPreviewEditIndex(previewIndex);
    setPreviewEditForm({ ...target });
    setCurModalOpen('preview');
  };

  const closePreviewEditModal = () => {
    setCurModalOpen('none');
    setPreviewEditIndex(null);
    setPreviewEditForm(EMPTY_PREVIEW_ITEM);
  };

  const handlePreviewEditSubmit = () => {
    if (previewEditIndex === null || !previewItems) {
      closePreviewEditModal();
      return;
    }

    setPreviewItems((prev) =>
      prev
        ? prev.map((item, index) =>
            index === previewEditIndex ? { ...previewEditForm } : item
          )
        : prev
    );
    closePreviewEditModal();
  };

  const handlePreviewEditChange =
    (field: keyof UploadCustomCodesPreviewItem) =>
    (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setPreviewEditForm((prev) => ({
        ...prev,
        [field]: event.target.value,
      }));

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
  });

  useEffect(() => {
    if (step === 'preview') {
      setSearchText('');
    }
  }, [step, setSearchText]);

  const uploading = isUploading || isUploadPending;
  const isEditSaveDisabled =
    !previewEditForm.code ||
    !previewEditForm.name ||
    !previewEditForm.system_key;

  const previewDisplayItems = searchText
    ? previewSearchResults
    : previewItems.map((i) => {
        return { item: i, matches: undefined };
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
            accept=".csv"
            hidden
            onChange={handleFileChange}
          />
        </>
        {uploading ? (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-8 text-center">
            <div className="mb-4 flex justify-center">
              <img
                src={UploadSvg}
                alt=""
                className="h-17 w-13.5"
                aria-hidden="true"
              />
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
            />
            {error && <div className="text-sm text-red-600">{error}</div>}
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
              {error && <p className="text-sm text-red-700">{error}</p>}
            </div>
            {uploadRowErrors && uploadRowErrors.length > 0 ? (
              <>
                <hr className="border-gray-cool-20" />
                <table className="w-full border-spacing-y-2 text-left text-sm">
                  <tbody>
                    {uploadRowErrors.map(({ row, error }) => (
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
                onClick={() => setCurModalOpen('confirm')}
                disabled={isConfirming}
              >
                Confirm & save codes
              </Button>
              <Button
                variant="tertiary"
                onClick={() => setCurModalOpen('undo')}
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
                {previewDisplayItems.map(({ item, matches }, idx) => (
                  <tr
                    key={`code-${item.system_key}-${idx} ?? row}`}
                    className="border-y border-blue-50"
                  >
                    <td className="px-2 py-1">
                      {highlightMatches(item.code, matches, 'code')}
                    </td>
                    <td className="px-2 py-1">{item.system_display_name}</td>
                    <td className="px-2 py-1">
                      {highlightMatches(item.name, matches, 'name')}
                    </td>
                    <td className="px-2 py-1 text-right text-sm">
                      <Button
                        variant="tertiary"
                        onClick={() => openPreviewEditModal(idx)}
                      >
                        Edit
                      </Button>
                      <span className="px-2 text-gray-400">&nbsp;</span>
                      <Button
                        variant="tertiary"
                        onClick={() => {
                          const updated =
                            previewItems?.filter((_, idx) => idx !== idx) ?? [];
                          if (updated.length === 0) {
                            setPreviewItems([]);
                            setUploadRowErrors(null);
                            setError(null);
                            setStep('intro');
                            onSuccess?.();
                          } else {
                            setPreviewItems(updated);
                          }
                          showToast({
                            heading: 'Row deleted',
                            body: item.code,
                          });
                        }}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {error && <div className="text-sm text-red-600">{error}</div>}
          </div>
        ) : null}
      </div>

      <ConfirmModal
        isOpen={curOpenModal === 'confirm'}
        onClose={() => setCurModalOpen('none')}
        handleConfirm={handleConfirm}
      />

      <UndoModal
        isOpen={curOpenModal === 'undo'}
        onClose={() => setCurModalOpen('none')}
        handleDelete={handleDelete}
      />

      <PreviewEditModal
        isOpen={curOpenModal === 'preview'}
        closePreviewEditModal={closePreviewEditModal}
        previewEditForm={previewEditForm}
        setPreviewEditForm={setPreviewEditForm}
        isEditSaveDisabled={isEditSaveDisabled}
        handlePreviewEditSubmit={handlePreviewEditSubmit}
        previewItems={previewItems}
        previewEditIndex={previewEditIndex}
        setError={setError}
        error={error}
        handlePreviewEditChange={handlePreviewEditChange}
      />
    </>
  );
}

type UploadInstructionProps = {
  handleButtonClick: () => void;
  disabled: boolean;
};

function UploadInstructions({
  handleButtonClick,
  disabled,
}: UploadInstructionProps) {
  const downloadTemplate = () => {
    const blob = new Blob([UPLOAD_TEMPLATE_CSV_CONTENT], {
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
          <Button variant="secondary" type="button" onClick={downloadTemplate}>
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

import { useQueryClient } from '@tanstack/react-query';
import { FuseResultMatch, IFuseOptions } from 'fuse.js';
import { useRef, useState, useEffect, ChangeEvent, useMemo } from 'react';
import {
  useUploadCustomCodesCsv,
  useConfirmUploadCustomCodesCsv,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import { CodeSystem } from '../../../../api/schemas';
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
import { Button } from '../../../../components/Button';
import { ModalRef } from '@trussworks/react-uswds';
import { CsvImportStep } from '../';
import UploadSvg from '../../../../assets/upload.svg';
import { Search } from '../../../../components/Search';

type PreviewRow = {
  item: SearchPreviewItem;
  matches?: readonly FuseResultMatch[];
};

const PREVIEW_CODE_SYSTEMS: CodeSystem[] = Object.values(CodeSystem);

const EMPTY_PREVIEW_FORM: UploadCustomCodesPreviewItem = {
  code: '',
  system: CodeSystem['Other'],
  name: '',
};

interface ImportCustomCodesProps {
  configurationId: string;
  disabled?: boolean;
  onSuccess?: () => void;
  onStepChange?: (step: CsvImportStep) => void;
}

type PreviewError = { row: number; error: string };

type SearchPreviewItem = UploadCustomCodesPreviewItem & {
  previewIndex: number;
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

  const [error, setError] = useState<string | null>(null);
  const [apiErrors, setApiErrors] = useState<PreviewError[] | null>(null);
  const [previewItems, setPreviewItems] = useState<
    UploadCustomCodesPreviewItem[] | null
  >(null);
  const [step, setStep] = useState<CsvImportStep>('intro');
  const [isUploading, setIsUploading] = useState(false);
  const [previewEditIndex, setPreviewEditIndex] = useState<number | null>(null);
  const [previewEditForm, setPreviewEditForm] =
    useState<UploadCustomCodesPreviewItem>({
      code: '',
      system: 'ICD-10',
      name: '',
    });
  const previewEditModalRef = useRef<ModalRef | null>(null);
  const confirmModalRef = useRef<ModalRef | null>(null);
  const undoModalRef = useRef<ModalRef | null>(null);

  const { mutate: uploadCsvMutation, isPending: isUploadPending } =
    useUploadCustomCodesCsv();
  const { mutate: confirmCsvMutation, isPending: isConfirming } =
    useConfirmUploadCustomCodesCsv();

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

  const uploading = isUploading || isUploadPending;

  const renderCsvInstructions = () => (
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
            onClick={handleDownloadTemplate}
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

  const handleButtonClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

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

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a valid CSV file.');
      setApiErrors(null);
      return;
    }

    setError(null);
    setApiErrors(null);
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
          const preview = res.data.preview ?? [];
          if (preview.length === 0) {
            setError('The CSV file did not produce any valid rows.');
            return;
          }
          setPreviewItems(preview);
          setStep('preview');
          setApiErrors(null);
        },
        onError: (err: unknown) => {
          const csvError = err as UploadCsvError;
          const parsedErrors = csvError.response?.data?.detail?.errors;
          if (parsedErrors?.length) {
            const parsed = parsedErrors.map(({ row, error }) => ({
              row: Number(row),
              error: String(error),
            }));
            setApiErrors(parsed);
            setStep('error');
            showToast({
              variant: 'error',
              heading: 'Error importing CSV',
              body: `${parsed.length} errors`,
            });
            return;
          }
          const message = formatApiError(err);
          setError(message);
          setApiErrors(null);
          showToast({
            variant: 'error',
            heading: 'Error uploading CSV',
            body: message,
          });
        },
        onSettled: () => {
          setIsUploading(false);
        },
      }
    );
  };

  const handleDownloadTemplate = () => {
    const csv = `code_number,code_system,display_name
12345,Other,Other Example
6789,ICD-10,ICD-10 Example
99999A,LOINC,LOINC Example`;

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'custom_code_upload_template.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);
  };

  const openConfirmModal = () => {
    confirmModalRef.current?.toggleModal();
  };

  const closeConfirmModal = () => {
    confirmModalRef.current?.toggleModal();
  };

  const openUndoModal = () => {
    undoModalRef.current?.toggleModal();
  };

  const closeUndoModal = () => {
    undoModalRef.current?.toggleModal();
  };

  const handleConfirm = () => {
    if (!previewItems?.length) return;

    closeConfirmModal();

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
    setPreviewItems(null);
    setApiErrors(null);
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
    previewEditModalRef.current?.toggleModal();
  };

  const closePreviewEditModal = () => {
    previewEditModalRef.current?.toggleModal();
    setPreviewEditIndex(null);
    setPreviewEditForm(EMPTY_PREVIEW_FORM);
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

  const previewData = useMemo<SearchPreviewItem[]>(() => {
    if (!previewItems) return [];
    return previewItems.map((item, index) => ({
      ...item,
      previewIndex: index,
    }));
  }, [previewItems]);

  const previewSearchOptions = useMemo<IFuseOptions<SearchPreviewItem>>(
    () => ({
      keys: [
        { name: 'code', weight: 0.6 },
        { name: 'name', weight: 0.4 },
      ],
      includeMatches: true,
      minMatchCharLength: 2,
    }),
    []
  );

  const {
    searchText,
    setSearchText,
    results: previewSearchResults,
  } = useSearch<SearchPreviewItem>(previewData, previewSearchOptions);

  useEffect(() => {
    if (step === 'preview') {
      setSearchText('');
    }
  }, [step, setSearchText]);

  const previewRows = useMemo<PreviewRow[]>(() => {
    if (searchText) {
      return previewSearchResults.map(({ item, matches }) => ({
        item,
        matches,
      }));
    }

    return previewData.map((item) => ({ item }));
  }, [previewData, previewSearchResults, searchText]);

  const isEditSaveDisabled =
    !previewEditForm.code || !previewEditForm.name || !previewEditForm.system;

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
                className="h-[68px] w-[54px]"
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
            {renderCsvInstructions()}
            {error && <div className="text-sm text-red-600">{error}</div>}
          </div>
        ) : step === 'error' ? (
          <div className="flex flex-col gap-6">
            <p className="font-bold">
              Please fix the errors in your CSV and re-upload it.
            </p>
            <Button
              onClick={handleButtonClick}
              disabled={disabled}
              variant="primary"
              className="max-w-40 px-5"
            >
              Re-upload CSV
            </Button>
            <div className="mb-2">
              {error && <p className="text-sm text-red-700">{error}</p>}
            </div>
            {apiErrors && apiErrors.length > 0 ? (
              <>
                <hr className="border-gray-cool-20" />
                <table className="w-full border-spacing-y-2 text-left text-sm">
                  <tbody>
                    {apiErrors.map(({ row, error }) => (
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
                onClick={openConfirmModal}
                disabled={isConfirming}
              >
                Confirm & save codes
              </Button>
              <Button variant="tertiary" onClick={openUndoModal}>
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
                  className="w-full min-w-[240px]"
                />
              </div>
            </div>
            <table className="w-full border-separate border-spacing-y-2 text-left text-sm">
              <tbody>
                {previewRows.map(({ item, matches }) => (
                  <tr
                    key={`${item.code}-${item.system}-${item.previewIndex ?? item.row}`}
                    className="border-y border-blue-50"
                  >
                    <td className="px-2 py-1">
                      {highlightMatches(item.code, matches, 'code')}
                    </td>
                    <td className="px-2 py-1">{item.system}</td>
                    <td className="px-2 py-1">
                      {highlightMatches(item.name, matches, 'name')}
                    </td>
                    <td className="px-2 py-1 text-right text-sm">
                      <Button
                        variant="tertiary"
                        onClick={() => openPreviewEditModal(item.previewIndex)}
                      >
                        Edit
                      </Button>
                      <span className="px-2 text-gray-400">&nbsp;</span>
                      <Button
                        variant="tertiary"
                        onClick={() => {
                          const updated =
                            previewItems?.filter(
                              (_, idx) => idx !== item.previewIndex
                            ) ?? [];
                          if (updated.length === 0) {
                            setPreviewItems(null);
                            setApiErrors(null);
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
        confirmModalRef={confirmModalRef}
        closeConfirmModal={closeConfirmModal}
        handleConfirm={handleConfirm}
      />

      <UndoModal
        undoModalRef={undoModalRef}
        closeUndoModal={closeUndoModal}
        handleDelete={handleDelete}
      />

      <PreviewEditModal
        previewEditModalRef={previewEditModalRef}
        closePreviewEditModal={closePreviewEditModal}
        previewEditForm={previewEditForm}
        setPreviewEditForm={setPreviewEditForm}
        isEditSaveDisabled={isEditSaveDisabled}
        handlePreviewEditSubmit={handlePreviewEditSubmit}
        PREVIEW_CODE_SYSTEMS={PREVIEW_CODE_SYSTEMS}
        previewItems={previewItems}
        previewEditIndex={previewEditIndex}
        setError={setError}
        error={error}
        handlePreviewEditChange={handlePreviewEditChange}
      />
    </>
  );
}

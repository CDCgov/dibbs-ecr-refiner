import { useParams } from 'react-router';
import EicrSectionReview from './EicrSectionReview';
import { Title } from '../../../components/Title';
import { Button, SECONDARY_BUTTON_STYLES } from '../../../components/Button';
import { useToast } from '../../../hooks/useToast';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useRef, useEffect, useMemo, useState, forwardRef } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import {
  Modal,
  ModalRef,
  ModalHeading,
  ModalToggleButton,
  ModalFooter,
  Label,
  TextInput,
  Select,
  Icon,
} from '@trussworks/react-uswds';
import { useSearch } from '../../../hooks/useSearch';
import {
  getGetConfigurationQueryKey,
  useAddCustomCodeToConfiguration,
  useDeleteCustomCodeFromConfiguration,
  useDisassociateConditionWithConfiguration,
  useEditCustomCodeFromConfiguration,
  useGetConfiguration,
} from '../../../api/configurations/configurations';
import {
  AddCustomCodeInputSystem,
  DbConfigurationCustomCode,
  DbConfigurationCustomCodeSystem,
  GetConfigurationResponse,
} from '../../../api/schemas';
import { useGetCondition } from '../../../api/conditions/conditions';
import { useDebouncedCallback } from 'use-debounce';
import { FuseResultMatch } from 'fuse.js';
import { AddConditionCodeSetsDrawer } from './AddConditionCodeSets';
import { highlightMatches } from '../../../utils/highlight';
import { useQueryClient } from '@tanstack/react-query';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../titleBar';
import { Spinner } from '../../../components/Spinner';
import ErrorFallback from '../../ErrorFallback';

export default function ConfigBuild() {
  const { id } = useParams<{ id: string }>();
  const {
    data: response,
    isPending,
    isError,
    error,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return <ErrorFallback error={error} />;

  // sort so the default code set always displays first
  const sortedCodeSets = response.data.code_sets.sort((a) => {
    return a.display_name === response.data.display_name ? -1 : 1;
  });

  return (
    <div>
      <TitleContainer>
        <Title>{response.data.display_name}</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={response.data.id} />
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <div className="content flex flex-wrap justify-between">
          <ConfigurationTitleBar step="build" />
          <Export id={id} />
        </div>
        <Builder
          id={id}
          code_sets={sortedCodeSets}
          included_conditions={response.data.included_conditions}
          custom_codes={response.data.custom_codes}
          section_processing={response.data.section_processing}
          display_name={response.data.display_name}
          loinc_codes={response.data.loinc_codes}
        />
      </SectionContainer>
    </div>
  );
}

type ExportBuilderProps = {
  id: string;
};

export function Export({ id }: ExportBuilderProps) {
  return (
    <a
      className="text-blue-cool-60 mt-8 mb-6 self-end font-bold hover:cursor-pointer hover:underline"
      href={`/api/v1/configurations/${id}/export`}
      download
    >
      Export configuration
    </a>
  );
}

type BuilderProps = GetConfigurationResponse;

function Builder({
  id,
  code_sets,
  custom_codes,
  included_conditions,
  section_processing,
  display_name: default_condition_name,
  loinc_codes,
}: BuilderProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [tableView, setTableView] = useState<
    'none' | 'codeset' | 'custom' | 'sections'
  >('none');
  const [selectedCodesetId, setSelectedCodesetId] = useState<string | null>(
    null
  );
  const [selectedCodesetName, setSelectedCodesetName] = useState<string | null>(
    null
  );
  const modalRef = useRef<ModalRef | null>(null);
  const codeSetButtonRefs = useRef<Record<string, HTMLButtonElement | null>>(
    {}
  );

  function onCodesetClick(name: string, id: string) {
    setSelectedCodesetName(name);
    setSelectedCodesetId(id);
    setTableView('codeset');
  }

  function onCustomCodeClick() {
    setSelectedCodesetName(null);
    setSelectedCodesetId(null);
    setTableView('custom');
  }

  function setCodesetListItemFocus(deletedId: string) {
    const deletedItemIndex = code_sets.findIndex(
      (c) => c.condition_id === deletedId
    );

    /**
     * This shouldn't happen since we can't delete the primary condition code set.
     * Just in case 🙂
     */
    if (deletedItemIndex <= 0) return;

    const previousCodeSetId = code_sets[deletedItemIndex - 1].condition_id;

    codeSetButtonRefs.current[previousCodeSetId]?.click();
  }

  useEffect(() => {
    if (tableView === 'none' && code_sets[0] && code_sets[0].condition_id) {
      onCodesetClick(code_sets[0].display_name, code_sets[0].condition_id);
    }
  }, [code_sets, default_condition_name, tableView]);

  return (
    <div className="bg-blue-cool-5 h-[35rem] rounded-lg p-4">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col py-2 pt-4 md:w-[20rem] md:gap-10">
          <div className="h-50 overflow-scroll md:h-[35rem]">
            <OptionsLabelContainer>
              <OptionsLabel htmlFor="open-codesets">
                CONDITION CODE SETS
              </OptionsLabel>
              <Button
                variant="secondary"
                className="text-blue-cool-60 !mr-0 flex h-8 flex-row items-center !px-3 !py-2 font-bold hover:cursor-pointer"
                id="open-codesets"
                aria-label="Add new code set to configuration"
                onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              >
                ADD
              </Button>
            </OptionsLabelContainer>
            <OptionsListContainer>
              <OptionsList>
                {code_sets.map((codeSet, i) => (
                  <li
                    key={codeSet.display_name}
                    className={classNames(
                      'group drop-shadow-base relative flex items-center overflow-visible rounded-sm hover:bg-stone-50',
                      {
                        'bg-white': selectedCodesetId === codeSet.condition_id,
                      }
                    )}
                  >
                    <ConditionCodeSetButton
                      ref={(btn) => {
                        codeSetButtonRefs.current[codeSet.condition_id] = btn;
                      }}
                      codeSetName={codeSet.display_name}
                      codeSetTotalCodes={codeSet.total_codes}
                      onViewCodeSet={() =>
                        onCodesetClick(
                          codeSet.display_name,
                          codeSet.condition_id
                        )
                      }
                      aria-controls={
                        selectedCodesetId ? 'codeset-table' : undefined
                      }
                    />
                    {i === 0 ? (
                      <span className="text-gray-cool-40 mr-2 hidden italic group-hover:block">
                        Default
                      </span>
                    ) : (
                      <DeleteCodeSetButton
                        configurationId={id}
                        conditionId={codeSet.condition_id}
                        conditionName={codeSet.display_name}
                        onClick={() =>
                          setCodesetListItemFocus(codeSet.condition_id)
                        }
                      />
                    )}
                  </li>
                ))}
              </OptionsList>
            </OptionsListContainer>
          </div>
          <div>
            <OptionsLabelContainer>
              <OptionsLabel>MORE OPTIONS</OptionsLabel>
            </OptionsLabelContainer>
            <OptionsListContainer>
              <OptionsList>
                <li key="custom-codes">
                  <button
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': tableView === 'custom',
                      }
                    )}
                    onClick={onCustomCodeClick}
                    aria-controls={
                      tableView === 'custom' ? 'custom-table' : undefined
                    }
                    aria-pressed={tableView === 'custom'}
                  >
                    <span>Custom codes</span>
                    <span>{custom_codes.length}</span>
                  </button>
                </li>
                <li key="sections">
                  <button
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': tableView === 'sections',
                      }
                    )}
                    onClick={() => {
                      setSelectedCodesetId(null);
                      setTableView('sections');
                    }}
                    aria-controls={
                      tableView === 'sections' ? 'sections-table' : undefined
                    }
                    aria-pressed={tableView === 'sections'}
                  >
                    <span>Sections</span>
                  </button>
                </li>
              </OptionsList>
            </OptionsListContainer>
          </div>
        </div>
        <div className="flex !h-full !max-h-[34.5rem] !w-full flex-col items-start overflow-y-scroll rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          {selectedCodesetId && tableView === 'codeset' ? (
            <>
              <ConditionCodeTable
                defaultCondition={selectedCodesetName}
                conditionId={selectedCodesetId}
              />
            </>
          ) : tableView === 'custom' ? (
            <>
              <h3 className="mb-2 text-xl font-bold">Custom codes</h3>
              <CustomCodeGroupingParagraph />
              <ModalToggleButton
                modalRef={modalRef}
                opener
                className={classNames('!mt-4', SECONDARY_BUTTON_STYLES)}
                aria-label="Add new custom code"
              >
                Add code
              </ModalToggleButton>
              <CustomCodesDetail
                configurationId={id}
                modalRef={modalRef}
                customCodes={custom_codes}
                loincCodes={loinc_codes}
              />
            </>
          ) : tableView === 'sections' ? (
            <>
              <EicrSectionReview
                configurationId={id}
                sectionProcessing={section_processing}
              />
            </>
          ) : null}
        </div>
      </div>
      <AddConditionCodeSetsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        conditions={included_conditions}
        configurationId={id}
      />
    </div>
  );
}

type ConditionCodeSetButtonProps = {
  codeSetName: string;
  codeSetTotalCodes: number;
  onViewCodeSet: () => void;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

const ConditionCodeSetButton = forwardRef<
  HTMLButtonElement,
  ConditionCodeSetButtonProps
>(
  (
    {
      codeSetName,
      codeSetTotalCodes,
      onViewCodeSet,
      ...props
    }: ConditionCodeSetButtonProps,
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={classNames(
          'group flex h-full w-full flex-row items-center justify-between gap-3 rounded p-1 text-left align-middle hover:cursor-pointer sm:p-4'
        )}
        onClick={onViewCodeSet}
        {...props}
      >
        <span aria-hidden>{codeSetName}</span>
        <span aria-hidden className="group-hover:hidden">
          {codeSetTotalCodes}
        </span>
        <span className="sr-only">
          {codeSetName}, {codeSetTotalCodes} codes in code set
        </span>
      </button>
    );
  }
);

interface DeleteCodeSetButtonProps {
  configurationId: string;
  conditionId: string;
  conditionName: string;
  onClick: () => void;
}

function DeleteCodeSetButton({
  configurationId,
  conditionId,
  conditionName,
  onClick,
}: DeleteCodeSetButtonProps) {
  const { mutate: disassociateMutation, isPending } =
    useDisassociateConditionWithConfiguration();
  const [isListInvalidating, setIsListInvalidating] = useState(false);

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  const isLoading = isPending || isListInvalidating;

  function handleDisassociateCondition(conditionId: string) {
    disassociateMutation(
      {
        configurationId,
        conditionId,
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition removed',
            body: resp.data.condition_name,
          });
          setIsListInvalidating(true);
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          setIsListInvalidating(false);
          onClick(); // set focus to previous code set button
        },
        onError: (error) => {
          setIsListInvalidating(false);
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error removing condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  if (isLoading) {
    return <Spinner size={20} className="mr-2" />;
  }

  return (
    <button
      className="text-gray-cool-40 sr-only !pr-4 group-hover:not-sr-only hover:cursor-pointer focus:not-sr-only"
      aria-label={`Delete code set ${conditionName}`}
      onClick={() => handleDisassociateCondition(conditionId)}
    >
      <Icon.Delete className="!fill-red-700" size={3} aria-hidden />
    </button>
  );
}

type OptionsLabelsProps = {
  children: React.ReactNode;
  htmlFor?: string;
};

function OptionsLabel({ children, htmlFor }: OptionsLabelsProps) {
  const styles = '!text-gray-600 text-base font-bold';

  if (!htmlFor) return <span className={styles}>{children}</span>;

  return (
    <label className={styles} htmlFor={htmlFor}>
      {children}
    </label>
  );
}

function OptionsLabelContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex w-full items-center justify-between">{children}</div>
  );
}

function OptionsListContainer({ children }: { children: React.ReactNode }) {
  return <div className="max-h-[30rem] overflow-y-scroll pt-2">{children}</div>;
}

function OptionsList({ children }: { children: React.ReactNode }) {
  return <ul className="flex flex-col gap-2">{children}</ul>;
}

interface CustomCodesDetailProps {
  configurationId: string;
  modalRef: React.RefObject<ModalRef | null>;
  customCodes: DbConfigurationCustomCode[];
  loincCodes: string[];
}

function CustomCodesDetail({
  configurationId,
  modalRef,
  customCodes,
  loincCodes,
}: CustomCodesDetailProps) {
  const { mutate: deleteCode } = useDeleteCustomCodeFromConfiguration();
  const [selectedCustomCode, setSelectedCustomCode] =
    useState<DbConfigurationCustomCode | null>(null);
  const queryClient = useQueryClient();
  const showToast = useToast();

  function toggleModal() {
    modalRef.current?.toggleModal();
    setSelectedCustomCode(null);
  }

  return (
    <>
      <table id="custom-table" className="!mt-6 w-full border-separate">
        <thead className="sr-only">
          <tr>
            <th>Custom code</th>
            <th>Custom code system</th>
            <th>Custom code name</th>
            <th>Modify the custom code</th>
          </tr>
        </thead>
        <tbody>
          {customCodes.map((customCode) => (
            <tr
              key={customCode.code + customCode.system}
              className="align-middle"
            >
              <td className="w-1/6 pb-6">{customCode.code}</td>
              <td className="text-gray-cool-60 w-1/6 pb-6">
                {customCode.system}
              </td>
              <td className="w-1/6 pb-6">{customCode.name}</td>
              <td className="w-1/2 text-right whitespace-nowrap">
                <ModalToggleButton
                  modalRef={modalRef}
                  opener
                  className="usa-button--unstyled !text-blue-cool-50 !mr-6 !font-bold !no-underline hover:!underline"
                  onClick={() => setSelectedCustomCode(customCode)}
                  aria-label={`Edit custom code ${customCode.name}`}
                >
                  Edit
                </ModalToggleButton>
                <button
                  className="!text-blue-cool-50 font-bold !no-underline hover:!cursor-pointer hover:!underline"
                  aria-label={`Delete custom code ${customCode.name}`}
                  onClick={() => {
                    deleteCode(
                      {
                        code: customCode.code,
                        system: customCode.system,
                        configurationId: configurationId,
                      },
                      {
                        onSuccess: async () => {
                          await queryClient.invalidateQueries({
                            queryKey:
                              getGetConfigurationQueryKey(configurationId),
                          });
                          showToast({
                            heading: 'Deleted code',
                            body: customCode.code,
                          });
                        },
                      }
                    );
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <CustomCodeModal
        configurationId={configurationId}
        initialCode={selectedCustomCode?.code}
        initialSystem={selectedCustomCode?.system}
        initialName={selectedCustomCode?.name}
        loincCodes={loincCodes}
        modalRef={modalRef}
        onClose={toggleModal}
      />
    </>
  );
}

function ConditionCodeGroupingParagraph() {
  return (
    <p>
      These condition code sets come from the default groupings in the{' '}
      <TesLink />
    </p>
  );
}

function CustomCodeGroupingParagraph() {
  return (
    <p>
      Add codes that are not included in the code sets from the <TesLink />
    </p>
  );
}

function TesLink() {
  return (
    <a
      className="text-blue-cool-60 hover:text-blue-cool-50 underline"
      href="https://tes.tools.aimsplatform.org/auth/signin"
      target="_blank"
      rel="noopener"
    >
      TES (Terminology Exchange Service).
    </a>
  );
}

interface ConditionCodeTableProps {
  conditionId: string;
  defaultCondition: string | null;
}

function ConditionCodeTable({
  conditionId,
  defaultCondition,
}: ConditionCodeTableProps) {
  const DEBOUNCE_TIME_MS = 300;

  const {
    data: response,
    isPending,
    isError,
    error,
  } = useGetCondition(conditionId);
  const [selectedCodeSystem, setSelectedCodeSystem] = useState<string>('all');
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const codes = useMemo(
    () => response?.data.codes ?? [],
    [response?.data.codes]
  );

  const filteredCodes = useMemo(() => {
    return selectedCodeSystem === 'all'
      ? codes
      : codes.filter((code) => code.system === selectedCodeSystem);
  }, [codes, selectedCodeSystem]);

  const { searchText, setSearchText, results } = useSearch(filteredCodes, {
    keys: [
      { name: 'code', weight: 0.7 },
      { name: 'description', weight: 0.3 },
    ],
    includeMatches: true,
    minMatchCharLength: 3,
  });

  const debouncedSearchUpdate = useDebouncedCallback((input: string) => {
    setIsLoadingResults(true);
    setSearchText(input);
    setHasSearched(true);
  }, DEBOUNCE_TIME_MS);

  useEffect(() => {
    if (isLoadingResults) {
      setIsLoadingResults(false);
    }
  }, [results, isLoadingResults]);

  // Show only the filtered codes if the user isn't searching
  const visibleCodes = searchText ? results.map((r) => r.item) : filteredCodes;

  if (isPending)
    return (
      <div className="flex w-full justify-center">
        <Spinner />
      </div>
    );
  if (isError) return <ErrorFallback error={error} />;

  function handleCodeSystemSelect(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedCodeSystem(event.target.value);
  }

  return (
    <div className="min-h-full min-w-full">
      <h3 className="text-xl font-bold">{defaultCondition} code set</h3>
      <div className="border-bottom-[1px] mb-4 flex min-w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
        <Search
          onChange={(e) => debouncedSearchUpdate(e.target.value)}
          id="code-search"
          name="code-search"
          placeholder="Search code set"
        />
        <div data-testid="code-system-select-container">
          <Label htmlFor="code-system-select">Code system</Label>
          <Select
            id="code-system-select"
            name="code-system-select"
            value={selectedCodeSystem}
            onChange={handleCodeSystemSelect}
          >
            <option key="all-code-systems" value="all">
              All code systems
            </option>
            {response.data.available_systems.map((system) => (
              <option key={system} value={system}>
                {system}
              </option>
            ))}
          </Select>
        </div>
      </div>
      <hr className="border-blue-cool-5 mb-6 w-full border-[1px]" />
      <ConditionCodeGroupingParagraph />

      {isLoadingResults ? (
        <div className="pt-10">
          <p>Loading...</p>
        </div>
      ) : hasSearched && searchText && (!results || results.length === 0) ? (
        <div className="pt-10">
          <p>No codes match the search criteria.</p>
        </div>
      ) : (
        <div role="region">
          <table
            id="codeset-table"
            className="w-full border-separate border-spacing-y-4"
            aria-label={`Codes in set with ID ${conditionId}`}
          >
            <thead className="sr-only">
              <tr>
                <th>Code</th>
                <th>Code system</th>
                <th>Condition</th>
              </tr>
            </thead>
            <tbody>
              {searchText
                ? results.map((r) => (
                    <ConditionCodeRow
                      key={`${r.item.system}-${r.item.code}`}
                      codeSystem={r.item.system}
                      code={r.item.code}
                      text={r.item.description}
                      matches={r.matches}
                    />
                  ))
                : visibleCodes.map((code) => (
                    <ConditionCodeRow
                      key={`${code.system}-${code.code}`}
                      codeSystem={code.system}
                      code={code.code}
                      text={code.description}
                    />
                  ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

interface CustomCodeModalProps {
  configurationId: string;
  modalRef: React.RefObject<ModalRef | null>;
  onClose: () => void;
  initialCode?: string;
  initialSystem?: string;
  initialName?: string;
  loincCodes: string[];
}

export function CustomCodeModal({
  configurationId,
  modalRef,
  onClose,
  initialCode,
  initialSystem,
  initialName,
  loincCodes,
}: CustomCodeModalProps) {
  const { mutate: addCode } = useAddCustomCodeToConfiguration();
  const { mutate: editCode } = useEditCustomCodeFromConfiguration();
  const queryClient = useQueryClient();
  const showToast = useToast();

  // TODO: this should come from the server.
  // Maybe get this info as part of the seed script?
  const systemValues = [
    { name: 'ICD-10', value: 'icd-10' },
    { name: 'SNOMED', value: 'snomed' },
    { name: 'RxNorm', value: 'rxnorm' },
    { name: 'LOINC', value: 'loinc' },
  ];

  const isEditing = initialCode && initialSystem && initialName;

  const [form, setForm] = useState({
    code: initialCode ?? '',
    system: initialSystem ? normalizeSystem(initialSystem) : 'icd-10',
    name: initialName ?? '',
  });

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm({
      code: initialCode ?? '',
      system: initialSystem ? normalizeSystem(initialSystem) : 'icd-10',
      name: initialName ?? '',
    });
  }, [initialCode, initialSystem, initialName]);

  function resetForm() {
    setForm({ code: '', system: 'icd-10', name: '' });
  }

  const isButtonEnabled = form.code && form.system && form.name;

  const handleChange =
    (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (isEditing) {
      editCode(
        {
          configurationId,
          data: {
            code: initialCode,
            system: normalizeSystem(initialSystem),
            new_code: form.code,
            new_system: normalizeSystem(form.system),
            new_name: form.name,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code updated', body: form.code });
            resetForm();
            onClose();
          },
          onError: () => {
            showToast({
              variant: 'error',
              heading: 'Custom code update failed',
              body: 'The code/system pair already exists.',
            });
            resetForm();
            onClose();
          },
        }
      );
    } else {
      addCode(
        {
          configurationId,
          data: {
            code: form.code,
            system: normalizeSystem(form.system),
            name: form.name,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code added', body: form.code });
            resetForm();
            onClose();
          },
        }
      );
    }
  };

  return (
    <Modal
      ref={modalRef}
      id="custom-code-modal"
      aria-describedby="modal-heading"
      aria-labelledby="modal-heading"
      isLarge
      className="!max-w-[25rem] !rounded-none p-10"
      forceAction
    >
      <ModalHeading
        id="modal-heading"
        className="text-bold font-merriweather mb-6 !p-0 text-xl"
      >
        {isEditing ? 'Edit custom code' : 'Add custom code'}
      </ModalHeading>

      <button
        type="button"
        aria-label="Close this window"
        onClick={() => {
          resetForm();
          onClose();
        }}
        className="absolute top-4 right-4 h-6 w-6 rounded text-gray-500 hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900 focus:outline focus:outline-indigo-500"
      >
        <Icon.Close className="!h-6 !w-6" aria-hidden />
      </button>

      <div className="mt-5 flex flex-col gap-5 !p-0">
        <div>
          <Label htmlFor="code">Code #</Label>
          <TextInput
            id="code"
            name="code"
            type="text"
            value={form.code}
            onChange={(e) => {
              setForm((prev) => ({ ...prev, code: e.target.value }));
              if (error) setError(''); // clear error on change
            }}
            onBlur={() => {
              if (loincCodes.includes(form.code)) {
                setError(
                  `The code "${form.code}" already exists in the condition code set.`
                );
              }
            }}
            autoComplete="off"
          />
          {error && (
            <p className="font-merriweather mb-1 text-sm text-red-600">
              {error}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="system">Code system</Label>
          <Select
            id="system"
            name="system"
            value={form.system}
            onChange={handleChange('system')}
          >
            {systemValues.map((sv) => (
              <option key={sv.value} value={sv.value}>
                {sv.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="name">Code name</Label>
          <TextInput
            id="name"
            name="name"
            type="text"
            value={form.name}
            onChange={handleChange('name')}
            autoComplete="off"
          />
        </div>
      </div>

      <ModalFooter className="flex justify-end p-0">
        <Button
          onClick={handleSubmit}
          disabled={!isButtonEnabled || !!error} // disable if form invalid or error exists
          variant={!isButtonEnabled || !!error ? 'disabled' : 'primary'}
          className="!m-0"
        >
          {isEditing ? 'Update' : 'Add custom code'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

interface ConditionCodeRowProps {
  code: string;
  codeSystem: string;
  text: string;
  matches?: readonly FuseResultMatch[];
}

function ConditionCodeRow({
  code,
  codeSystem,
  text,
  matches,
}: ConditionCodeRowProps) {
  return (
    <tr>
      <td className="w-1/6 pb-6">{highlightMatches(code, matches, 'code')}</td>
      <td className="text-gray-cool-60 w-1/6 pb-6">{codeSystem}</td>
      <td className="w-4/6 pb-6">
        {highlightMatches(text, matches, 'description')}
      </td>
    </tr>
  );
}

function normalizeSystem(
  system: DbConfigurationCustomCodeSystem | string
): AddCustomCodeInputSystem {
  return system.toLowerCase() as AddCustomCodeInputSystem;
}

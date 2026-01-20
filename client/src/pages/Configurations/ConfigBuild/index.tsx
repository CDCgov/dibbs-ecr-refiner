import { useParams } from 'react-router';
import { EicrSectionReview } from './EicrSectionReview';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { useToast } from '../../../hooks/useToast';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useRef, useMemo, useState, forwardRef } from 'react';

import classNames from 'classnames';
import { Search } from '../../../components/Search';
import {
  Modal,
  ModalRef,
  ModalHeading,
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
import { highlightMatches } from '../../../utils';
import { useQueryClient } from '@tanstack/react-query';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Spinner } from '../../../components/Spinner';
import { TesLink } from '../TesLink';
import { VersionMenu } from './VersionMenu';
import { DraftBanner } from './DraftBanner';
import { ConfigLockBanner } from './ConfigLockBanner';
import { Status } from './Status';
import { useConfigLockRelease } from '../../../hooks/useConfigLockRelease';
import { ModalToggleButton } from '../../../components/Button/ModalToggleButton';

export function ConfigBuild() {
  const { id } = useParams<{ id: string }>();

  // release lock on beforeunload
  useConfigLockRelease(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  const { is_locked: disabledForConcurrency } = configuration.data;
  const disabledForPrevVersion = configuration?.data.status !== 'draft';
  const isDisabled = disabledForConcurrency || disabledForPrevVersion;

  // sort so the default code set always displays first
  const sortedCodeSets = configuration.data.code_sets.sort((a) => {
    return a.display_name === configuration.data.display_name ? -1 : 1;
  });

  return (
    <>
      <TitleContainer>
        <Title>{configuration.data.display_name}</Title>
        <Status version={configuration.data.active_version} />
      </TitleContainer>
      <NavigationContainer>
        <VersionMenu
          id={configuration.data.id}
          currentVersion={configuration.data.version}
          status={configuration.data.status}
          versions={configuration.data.all_versions}
          step="build"
        />
        <StepsContainer>
          <Steps configurationId={configuration.data.id} />
        </StepsContainer>
      </NavigationContainer>
      {disabledForPrevVersion ? (
        <DraftBanner
          draftId={configuration.data.draft_id}
          conditionId={configuration.data.condition_id}
          latestVersion={configuration.data.latest_version}
          step="build"
        />
      ) : null}
      {disabledForConcurrency ? (
        <ConfigLockBanner
          lockedByName={configuration.data.locked_by?.name}
          lockedByEmail={configuration.data.locked_by?.email}
        />
      ) : null}
      <SectionContainer>
        <div className="content flex flex-wrap justify-between">
          <ConfigurationTitleBar
            step="build"
            condition={configuration.data.display_name}
          />
          <Export id={configuration.data.id} />
        </div>

        <Builder
          id={configuration.data.id}
          code_sets={sortedCodeSets}
          included_conditions={configuration.data.included_conditions}
          custom_codes={configuration.data.custom_codes}
          section_processing={configuration.data.section_processing}
          display_name={configuration.data.display_name}
          deduplicated_codes={configuration.data.deduplicated_codes}
          disabled={isDisabled}
        />
      </SectionContainer>
    </>
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

type BuilderProps = Pick<
  GetConfigurationResponse,
  | 'id'
  | 'code_sets'
  | 'custom_codes'
  | 'included_conditions'
  | 'section_processing'
  | 'display_name'
  | 'deduplicated_codes'
> & { disabled?: boolean };

function Builder({
  id,
  code_sets,
  custom_codes,
  included_conditions,
  section_processing,
  display_name: default_condition_name,
  deduplicated_codes,
  disabled,
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

  // initialize table with the first code set if 1) nothing is loaded and 2) the data is loaded
  if (tableView === 'none' && code_sets[0] && code_sets[0].condition_id) {
    onCodesetClick(code_sets[0].display_name, code_sets[0].condition_id);
  }

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
    // No change needed if we're not viewing the code set
    if (deletedId !== selectedCodesetId) return;

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

  return (
    <div className="bg-blue-cool-5 h-140 rounded-lg p-4">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col py-2 pt-4 md:w-[20rem] md:gap-10">
          <div>
            <OptionsLabelContainer>
              <OptionsLabel htmlFor="open-codesets">
                CONDITION CODE SETS
              </OptionsLabel>
              {!disabled && (
                <Button
                  variant="secondary"
                  className="text-blue-cool-60 mr-0! flex h-8 flex-row items-center px-3! py-2! font-bold hover:cursor-pointer"
                  id="open-codesets"
                  aria-label="Add new code set to configuration"
                  onClick={() => setIsDrawerOpen(!isDrawerOpen)}
                >
                  ADD
                </Button>
              )}
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

                    <DeleteCodeSetButton
                      index={i}
                      configurationId={id}
                      conditionId={codeSet.condition_id}
                      conditionName={codeSet.display_name}
                      onClick={() =>
                        setCodesetListItemFocus(codeSet.condition_id)
                      }
                      disabled={disabled}
                    />
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
        <div className="flex h-full! max-h-138! w-full! flex-col items-start overflow-y-scroll rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
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
                variant="secondary"
                className={classNames('mt-4!')}
                aria-label="Add new custom code"
                disabled={disabled}
              >
                Add code
              </ModalToggleButton>
              <CustomCodesDetail
                configurationId={id}
                modalRef={modalRef}
                customCodes={custom_codes}
                deduplicated_codes={deduplicated_codes}
                disabled={disabled}
              />
            </>
          ) : tableView === 'sections' ? (
            <EicrSectionReview
              configurationId={id}
              sectionProcessing={section_processing}
              disabled={disabled}
            />
          ) : null}
        </div>
      </div>
      <AddConditionCodeSetsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        conditions={included_conditions}
        configurationId={id}
        reportable_condition_display_name={default_condition_name}
        disabled={disabled}
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
        aria-label={`View TES code set information for ${codeSetName}`}
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
  index: number;
  configurationId: string;
  conditionId: string;
  conditionName: string;
  onClick: () => void;
  disabled?: boolean;
}

function DeleteCodeSetButton({
  index,
  configurationId,
  conditionId,
  conditionName,
  onClick,
  disabled,
}: DeleteCodeSetButtonProps) {
  const { mutate: disassociateMutation, isPending } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  function handleDisassociateCondition(conditionId: string) {
    disassociateMutation(
      {
        configurationId,
        conditionId,
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition code set removed',
            body: resp.data.condition_name,
          });

          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });

          onClick(); // set focus to previous code set button
        },
        onError: (error) => {
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

  if (isPending) {
    return <Spinner size={20} className="mr-2" />;
  }

  if (disabled) {
    return <></>;
  }

  return index === 0 ? (
    <span className="text-gray-cool-40 mr-2 hidden italic group-hover:block">
      Default
    </span>
  ) : (
    <button
      className="text-gray-cool-40 sr-only pr-4! group-hover:not-sr-only hover:cursor-pointer focus:not-sr-only disabled:cursor-not-allowed"
      aria-label={`Delete code set ${conditionName}`}
      onClick={() => handleDisassociateCondition(conditionId)}
      disabled={disabled}
    >
      <Icon.Delete
        className={disabled ? 'text-gray-cool-40' : 'fill-red-700!'}
        size={3}
        aria-hidden
      />
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
  return <div className="max-h-60 overflow-y-scroll pt-2">{children}</div>;
}

function OptionsList({ children }: { children: React.ReactNode }) {
  return <ul className="flex flex-col gap-2">{children}</ul>;
}

interface CustomCodesDetailProps {
  configurationId: string;
  modalRef: React.RefObject<ModalRef | null>;
  customCodes: DbConfigurationCustomCode[];
  deduplicated_codes: string[];
  disabled?: boolean;
}

function CustomCodesDetail({
  configurationId,
  modalRef,
  customCodes,
  deduplicated_codes,
  disabled,
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
      <table id="custom-table" className="mt-6! w-full border-separate">
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
                  opener={disabled}
                  variant="tertiary"
                  className="!mr-6"
                  onClick={() => {
                    if (disabled) return;
                    setSelectedCustomCode(customCode);
                  }}
                  aria-label={`Edit custom code ${customCode.name}`}
                >
                  Edit
                </ModalToggleButton>
                <Button
                  variant="tertiary"
                  aria-label={`Delete custom code ${customCode.name}`}
                  onClick={() => {
                    if (disabled) return;
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
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <CustomCodeModal
        configurationId={configurationId}
        selectedCustomCode={selectedCustomCode}
        deduplicated_codes={deduplicated_codes}
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

interface ConditionCodeTableProps {
  conditionId: string;
  defaultCondition: string | null;
}

function ConditionCodeTable({
  conditionId,
  defaultCondition,
}: ConditionCodeTableProps) {
  const DEBOUNCE_TIME_MS = 300;

  const { data: response, isPending, isError } = useGetCondition(conditionId);
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

  if (results && isLoadingResults) {
    setIsLoadingResults(false);
  }

  // Show only the filtered codes if the user isn't searching
  const visibleCodes = searchText ? results.map((r) => r.item) : filteredCodes;

  if (isPending)
    return (
      <div className="flex w-full justify-center">
        <Spinner />
      </div>
    );
  if (isError) return 'Error!';

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
      <hr className="border-blue-cool-5! mb-6 w-full border" />
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
            <thead className="bg-opacity-100 sticky -top-6 z-10 h-10 bg-white text-left">
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
  selectedCustomCode: DbConfigurationCustomCode | null;
  deduplicated_codes: string[];
}

export function CustomCodeModal({
  configurationId,
  modalRef,
  onClose,
  selectedCustomCode,
  deduplicated_codes,
}: CustomCodeModalProps) {
  const { mutate: addCode } = useAddCustomCodeToConfiguration();
  const { mutate: editCode } = useEditCustomCodeFromConfiguration();
  const queryClient = useQueryClient();
  const showToast = useToast();

  // TODO: this should come from the server.
  // Maybe get this info as part of the seed script?
  const systemValues = [
    { name: 'Select system', value: '' },
    { name: 'ICD-10', value: 'icd-10' },
    { name: 'SNOMED', value: 'snomed' },
    { name: 'RxNorm', value: 'rxnorm' },
    { name: 'LOINC', value: 'loinc' },
    { name: 'Other', value: 'other' },
  ];

  const [form, setForm] = useState({
    code: selectedCustomCode?.code ?? '',
    system: selectedCustomCode?.system
      ? normalizeSystem(selectedCustomCode.system)
      : '',
    name: selectedCustomCode?.name ?? '',
  });

  if (
    form.code === '' &&
    form.name === '' &&
    form.system === '' &&
    selectedCustomCode
  ) {
    setForm({
      code: selectedCustomCode?.code ?? '',
      system: selectedCustomCode?.system
        ? normalizeSystem(selectedCustomCode.system)
        : '',
      name: selectedCustomCode?.name ?? '',
    });
  }

  const [error, setError] = useState<string | null>(null);

  function resetForm() {
    setForm({ code: '', system: '', name: '' });
  }

  const isButtonEnabled =
    form.code && form.system && form.system !== '' && form.name;

  const handleChange =
    (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedCustomCode) {
      editCode(
        {
          configurationId,
          data: {
            code: selectedCustomCode.code,
            system: normalizeSystem(selectedCustomCode.system),
            name: selectedCustomCode.name,
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
      className="max-w-100! rounded-none! p-10"
      forceAction
    >
      <ModalHeading
        id="modal-heading"
        className="text-bold font-merriweather mb-6 p-0! text-xl"
      >
        {selectedCustomCode ? 'Edit custom code' : 'Add custom code'}
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
        <Icon.Close className="h-6! w-6!" aria-hidden />
      </button>

      <div className="mt-5 flex flex-col gap-5 p-0!">
        <div>
          <Label htmlFor="code">Code #</Label>
          <TextInput
            id="code"
            name="code"
            type="text"
            value={form.code}
            onChange={(e) => {
              const value = e.target.value.trimStart(); // trim leading space only while typing
              setForm((prev) => ({ ...prev, code: value }));
              if (error) setError(''); // clear error on change
            }}
            onBlur={() => {
              const trimmedCode = form.code.trim(); // full trim (leading + trailing)
              if (deduplicated_codes.includes(trimmedCode)) {
                setError(
                  `The code "${trimmedCode}" already exists in the condition code set.`
                );
              } else {
                setForm((prev) => ({ ...prev, code: trimmedCode })); // ensure stored value is clean
              }
            }}
            autoComplete="off"
          />
          {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
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
          variant="primary"
          className="m-0!"
        >
          {selectedCustomCode ? 'Update' : 'Add custom code'}
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

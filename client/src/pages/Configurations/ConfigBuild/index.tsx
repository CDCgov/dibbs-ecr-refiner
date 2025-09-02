import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { useToast } from '../../../hooks/useToast';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useRef, useEffect, useMemo, useState } from 'react';
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
  getGetConfigurationsQueryKey,
  useAddCustomCodeToConfiguration,
  useDeleteCustomCodeFromConfiguration,
  useGetConfiguration,
} from '../../../api/configurations/configurations';
import {
  DbConfigurationCustomCode,
  GetConfigurationResponse,
} from '../../../api/schemas';
import { useGetCondition } from '../../../api/conditions/conditions';
import { useDebouncedCallback } from 'use-debounce';
import { FuseResultMatch } from 'fuse.js';
import { useQueryClient } from '@tanstack/react-query';

export default function ConfigBuild() {
  const { id } = useParams<{ id: string }>();
  const {
    data: response,
    isLoading,
    isError,
  } = useGetConfiguration(id ?? '', {
    query: { enabled: !!id },
  });

  if (isLoading || !response?.data) return 'Loading...';
  if (!id || isError) return 'Error!';

  return (
    <div>
      <TitleContainer>
        <Title>{response.data.display_name}</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={response?.data.id} />
          <Button to={`/configurations/${id}/test`}>
            Next: Test configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <Builder
          id={id}
          code_sets={response.data.code_sets}
          custom_codes={response.data.custom_codes}
        />
      </SectionContainer>
    </div>
  );
}

type BuilderProps = Pick<
  GetConfigurationResponse,
  'id' | 'code_sets' | 'custom_codes'
>;

function Builder({ id, code_sets, custom_codes }: BuilderProps) {
  const [tableView, setTableView] = useState<'none' | 'codeset' | 'custom'>(
    'none'
  );
  const [selectedCodesetId, setSelectedCodesetId] = useState<string | null>(
    null
  );

  function onCodesetClick(id: string) {
    setSelectedCodesetId(id);
    setTableView('codeset');
  }

  function onCustomCodeClick() {
    setSelectedCodesetId(null);
    setTableView('custom');
  }

  return (
    <div className="bg-blue-cool-5 h-[35rem] rounded-lg p-2">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col gap-4 py-4 sm:w-1/3 md:px-2">
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <label
              className="text-gray-cool-60 font-bold"
              htmlFor="open-codesets"
            >
              CONDITION CODE SETS
            </label>
            <button
              className="text-blue-cool-60 flex flex-row items-center font-bold hover:cursor-pointer"
              id="open-codesets"
              aria-label="Add new code set to configuration"
            >
              <Icon.Add size={3} aria-hidden />
              <span>ADD</span>
            </button>
          </div>
          <div className="max-h-[10rem] overflow-y-auto md:max-h-[34.5rem]">
            <ul className="flex flex-col gap-2">
              {code_sets.map((codeSet) => (
                <li key={codeSet.display_name}>
                  <button
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': selectedCodesetId === codeSet.condition_id,
                      }
                    )}
                    onClick={() => onCodesetClick(codeSet.condition_id)}
                    aria-controls={
                      selectedCodesetId ? 'codeset-table' : undefined
                    }
                    aria-pressed={selectedCodesetId === codeSet.condition_id}
                  >
                    <span>{codeSet.display_name}</span>
                    <span>{codeSet.total_codes}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <label className="text-gray-cool-60 font-bold">MORE OPTIONS</label>
          </div>
          <div className="max-h-[10rem] overflow-y-auto md:max-h-[34.5rem]">
            <ul className="flex flex-col gap-2">
              <li key="custom-codes">
                <button
                  className={classNames(
                    'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                    {
                      'bg-white': tableView === 'custom',
                    }
                  )}
                  onClick={() => onCustomCodeClick()}
                  aria-controls={
                    tableView === 'custom' ? 'custom-table' : undefined
                  }
                  aria-pressed={tableView === 'custom'}
                >
                  <span>Custom codes</span>
                  <span>{custom_codes.length}</span>
                </button>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex max-h-[34.5rem] flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          {selectedCodesetId && tableView === 'codeset' ? (
            <>
              <ConditionCodeGroupingParagraph />
              <ConditionCodeTable conditionId={selectedCodesetId} />
            </>
          ) : tableView === 'custom' ? (
            <>
              <CustomCodesDetail
                configurationId={id}
                customCodes={custom_codes}
              />
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

interface CustomCodesTableProps {
  configurationId: string;
  customCodes: DbConfigurationCustomCode[];
}

function CustomCodesDetail({
  configurationId,
  customCodes,
}: CustomCodesTableProps) {
  const { mutate } = useDeleteCustomCodeFromConfiguration();
  const modalRef = useRef<ModalRef>(null);
  if (customCodes.length === 0) return null;

  return (
    <>
      <CustomCodeGroupingParagraph />
      <ModalToggleButton
        modalRef={modalRef}
        opener
        className="!bg-violet-warm-60 hover:!bg-violet-warm-70 !m-0"
      >
        Add code
      </ModalToggleButton>
      <table className="!mt-6 w-full border-separate">
        <tbody>
          {customCodes.map((customCode) => (
            <tr
              key={customCode.code + customCode.system}
              className="align-middle"
            >
              <td>{customCode.code}</td>
              <td>{customCode.system}</td>
              <td>{customCode.name}</td>
              <td className="text-right whitespace-nowrap">
                <button className="usa-button usa-button--unstyled text-blue-60 !mr-2">
                  Edit
                </button>
                <button
                  className="usa-button usa-button--unstyled text-red-60"
                  onClick={() => {
                    mutate({
                      code: customCode.code,
                      system: customCode.system,
                      configurationId: configurationId,
                    });
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <CustomCodeModal configurationId={configurationId} modalRef={modalRef} />
    </>
  );
}

function ConditionCodeGroupingParagraph() {
  return (
    <p>
      These condition code sets come from the default groupings in the{' '}
      <a
        className="text-blue-cool-60 hover:text-blue-cool-50 underline"
        href="https://tes.tools.aimsplatform.org/auth/signin"
        target="_blank"
        rel="noopener"
      >
        TES (Terminology Exchange Service).
      </a>
    </p>
  );
}

function CustomCodeGroupingParagraph() {
  return (
    <p>
      Add codes that are not included in the code sets from the{' '}
      <a
        className="text-blue-cool-60 hover:text-blue-cool-50 underline"
        href="https://tes.tools.aimsplatform.org/auth/signin"
        target="_blank"
        rel="noopener"
      >
        TES (Terminology Exchange Service).
      </a>
    </p>
  );
}

interface ConditionCodeTableProps {
  conditionId: string;
}

function ConditionCodeTable({ conditionId }: ConditionCodeTableProps) {
  const DEBOUNCE_TIME_MS = 300;

  const { data: response, isLoading, isError } = useGetCondition(conditionId);
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

  if (isLoading || !response?.data) return 'Loading...';
  if (isError) return 'Error!';

  function handleCodeSystemSelect(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedCodeSystem(event.target.value);
  }

  return (
    <div className="min-h-full min-w-full">
      <div className="border-bottom-[1px] mb-4 flex min-w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
        <Search
          onChange={(e) => debouncedSearchUpdate(e.target.value)}
          id="code-search"
          name="code-search"
          type="search"
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
      <hr className="border-blue-cool-5 w-full border-[1px]" />
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
      <td className="w-1/6">{highlightMatches(code, matches, 'code')}</td>
      <td className="w-1/6">{codeSystem}</td>
      <td className="w-4/6">
        {highlightMatches(text, matches, 'description')}
      </td>
    </tr>
  );
}

interface CustomCodeModalProps {
  configurationId: string;
  modalRef: React.RefObject<ModalRef | null>;
  initialData?: { code: string; system: string; name: string } | null;
}

export function CustomCodeModal({
  configurationId,
  modalRef,
  initialData,
}: CustomCodeModalProps) {
  const { mutate } = useAddCustomCodeToConfiguration();
  const queryClient = useQueryClient();
  const showToast = useToast();

  const [code, setCode] = useState(initialData?.code ?? '');
  const [system, setSystem] = useState(initialData?.system ?? '');
  const [name, setName] = useState(initialData?.name ?? '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    mutate(
      {
        configurationId: configurationId,
        data: {
          code: 'idkdk2q',
          name: 'test',
          system: 'snomed',
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationsQueryKey(),
          });
          showToast({
            heading: 'Custom code added',
            body: code,
          });
          modalRef.current?.toggleModal();
        },
      }
    );
  };

  return (
    <Modal
      ref={modalRef}
      id="add-custom-code-modal"
      aria-labelledby="add-custom-code-title"
      aria-describedby="Modal for adding custom code"
      isLarge
      className="!h-[30.125rem] !w-[35rem] !rounded-none"
      forceAction
    >
      <ModalHeading
        id="add-custom-code-title"
        className="text-bold font-merriweather mb-6 text-xl"
      >
        {initialData ? 'Edit custom code' : 'Add custom code'}
      </ModalHeading>

      <button
        type="button"
        aria-label="Close this window"
        onClick={() => modalRef.current?.toggleModal()}
        className="absolute top-4 right-4 rounded p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline focus:outline-indigo-500"
      >
        <Icon.Close className="h-5 w-5" aria-hidden />
      </button>

      <div className="mt-5 flex max-w-3/4 flex-col gap-5">
        <div className="max-w-3/4">
          <Label
            htmlFor="code"
            className="font-public-sans text-sm text-gray-700"
          >
            Code #
          </Label>
          <TextInput
            id="code"
            name="code"
            type="text"
            value={code}
            className="w-full rounded-md border px-3 py-2"
            onChange={(e) => setCode(e.target.value)}
          />
        </div>

        <div className="max-w-3/4">
          <Label
            htmlFor="system"
            className="font-public-sans text-sm text-gray-700"
          >
            Code system
          </Label>
          <Select
            id="system"
            name="system"
            value={system}
            className="w-full rounded-md border px-3 py-2"
            onChange={(e) => setSystem(e.target.value)}
          >
            <option value="">- Select -</option>
            <option value="icd10">ICD-10</option>
            <option value="snomed">SNOMED</option>
            <option value="loinc">LOINC</option>
            <option value="rxnorm">RxNorm</option>
          </Select>
        </div>

        <div className="max-w-3/4">
          <Label
            htmlFor="name"
            className="font-public-sans text-sm text-gray-700"
          >
            Code name
          </Label>
          <TextInput
            id="name"
            name="name"
            type="text"
            value={name}
            className="w-full rounded-md border px-3 py-2"
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <ModalFooter className="maxw-4/4 flex justify-end space-x-4 pt-6">
          <Button
            type="submit"
            variant={!code || !system || !name ? 'disabled' : 'primary'}
            disabled={!code || !system || !name}
            onClick={handleSubmit}
          >
            {initialData ? 'Update' : 'Add custom code'}
          </Button>
        </ModalFooter>
      </div>
    </Modal>
  );
}

function highlightMatches(
  text: string,
  matches?: readonly FuseResultMatch[],
  key?: string
) {
  if (!matches || !key) return text;

  const match = matches.find((m) => m.key === key);
  if (!match || !match.indices.length) return text;

  const indices = match.indices;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  indices.forEach(([start, end], i) => {
    if (lastIndex < start) {
      parts.push(text.slice(lastIndex, start));
    }
    parts.push(<mark key={i}>{text.slice(start, end + 1)}</mark>);
    lastIndex = end + 1;
  });

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

import { Search } from '@components/Search';
import { useSearch } from '../../../../hooks/useSearch';
import { useGetCondition } from '../../../../api/conditions/conditions';
import { useDebouncedCallback } from 'use-debounce';
import { highlightMatches } from '../../../../utils';
import { TesLink } from '../../TesLink';
import { useQueryClient } from '@tanstack/react-query';
import { useState, useMemo, useRef } from 'react';
import { CompletenessStatusBadge } from './CompletenessStatusBadge';
import {
  useDeleteCustomCodeFromConfiguration,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import {
  CodeSystemsReponse,
  DbCodeSystem,
  DbConfigurationCustomCode,
} from '../../../../api/schemas';
import { Spinner } from '@components/Spinner';
import { useToast } from '../../../../hooks/useToast';
import { Button } from '@components/Button';
import { CustomCodeModal } from './CustomCodeModal';
import { Select, SelectContainer } from '@components/Select';
import { Label } from '@components/Label';
import { Field } from '@components/Field';
import { useVirtualizer } from '@tanstack/react-virtual';

interface CustomCodesDetailProps {
  configurationId: string;
  customCodes: DbConfigurationCustomCode[];
  codeSystems: { [key: string]: DbCodeSystem };
  disabled: boolean;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

type ConfigurationCustomCodeDisplay = DbConfigurationCustomCode & {
  codeSystemDisplayName: string;
};

function enrichCustomCodeWithSystemDisplay(
  customCodes: DbConfigurationCustomCode[],
  codeSystems: { [key: string]: DbCodeSystem } | null
): ConfigurationCustomCodeDisplay[] {
  return customCodes.map((c) => {
    return {
      ...c,
      codeSystemDisplayName:
        codeSystems && Object.keys(codeSystems).includes(c.system_key)
          ? codeSystems[c.system_key].display_name
          : c.system_key,
    };
  });
}

export function CustomCodesDetail({
  configurationId,
  customCodes,
  codeSystems,
  disabled,
  isOpen,
  setIsOpen,
}: CustomCodesDetailProps) {
  const { mutate: deleteCode } = useDeleteCustomCodeFromConfiguration();
  const [selectedCustomCode, setSelectedCustomCode] =
    useState<ConfigurationCustomCodeDisplay | null>(null);
  const queryClient = useQueryClient();
  const showToast = useToast();

  const displayCustomCodes = enrichCustomCodeWithSystemDisplay(
    customCodes,
    codeSystems
  );

  const resetModal = () => {
    setSelectedCustomCode(null);
  };

  return (
    <div role="region">
      <table className="mt-6! w-full border-separate">
        <thead className="sr-only">
          <tr>
            <th>Custom code</th>
            <th>Custom code system</th>
            <th>Custom code name</th>
            <th>Modify the custom code</th>
          </tr>
        </thead>
        <tbody>
          {displayCustomCodes.map((customCode) => (
            <tr
              key={customCode.code + customCode.system_key}
              className="align-middle"
            >
              <td className="w-1/6 pb-6">{customCode.code}</td>
              <td className="text-gray-cool-60 w-1/6 pb-6">
                {customCode.codeSystemDisplayName}
              </td>
              <td className="w-1/6 pb-6">{customCode.name}</td>

              <td className="flex w-1/2 justify-end pb-6 whitespace-nowrap">
                {!disabled && (
                  <div className="flex flex-row gap-2">
                    <Button
                      variant="tertiary"
                      onClick={() => {
                        if (disabled) return;
                        setSelectedCustomCode(customCode);
                        setIsOpen(true);
                      }}
                      aria-label={`Edit custom code ${customCode.name}`}
                      disabled={disabled}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="tertiary"
                      aria-label={`Delete custom code ${customCode.name}`}
                      onClick={() => {
                        if (disabled) return;
                        deleteCode(
                          {
                            // encode to prevent special characters from breaking the action
                            code: encodeURIComponent(customCode.code),
                            systemKey: customCode.system_key,
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
                    <div className="sr-only">
                      Editing actions aren't available for previous versions
                    </div>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <CustomCodeModal
        isOpen={isOpen}
        setIsOpen={setIsOpen}
        configurationId={configurationId}
        selectedCustomCode={selectedCustomCode}
        onClose={resetModal}
      />
    </div>
  );
}

function ConditionCodeGroupingParagraph() {
  return (
    <p className="mb-6">
      These condition code sets come from the default groupings in the{' '}
      <TesLink />
    </p>
  );
}

interface ConditionCodeTableProps {
  conditionId: string;
  defaultCondition: string | null;
}

export function ConditionCodeTable({
  conditionId,
  defaultCondition,
}: ConditionCodeTableProps) {
  const DEBOUNCE_TIME_MS = 300;

  const { data: response, isPending, isError } = useGetCondition(conditionId);
  const [selectedCodeSystem, setSelectedCodeSystem] = useState<string>('all');
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const parentRef = useRef<HTMLDivElement>(null);

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
    threshold: 0.25,
    ignoreLocation: true,
  });

  const debouncedSearchUpdate = useDebouncedCallback((input: string) => {
    setIsLoadingResults(true);
    setSearchText(input);
    setHasSearched(true);
  }, DEBOUNCE_TIME_MS);

  if (results && isLoadingResults) {
    setIsLoadingResults(false);
  }

  function isCodeLikeQuery(value: string) {
    const trimmed = value.trim();
    return (
      /^[a-z0-9.-]+$/i.test(trimmed) &&
      !trimmed.includes(' ') &&
      !/[a-z]{2}/i.test(trimmed)
    );
  }

  const visibleCodes = useMemo(() => {
    const trimmedSearch = searchText.trim();
    if (!trimmedSearch) return filteredCodes;

    if (isCodeLikeQuery(trimmedSearch)) {
      const normalizedSearch = trimmedSearch.toLowerCase();
      return filteredCodes.filter((code) => {
        const normalizedCode = String(code.code).toLowerCase();
        return (
          normalizedCode === normalizedSearch ||
          normalizedCode.includes(normalizedSearch)
        );
      });
    }

    return results.map((r) => r.item);
  }, [filteredCodes, results, searchText]);

  const resultsByCode = useMemo(() => {
    return new Map(
      results.map((result) => [
        `${result.item.system}-${result.item.code}-${result.item.description}`,
        result,
      ])
    );
  }, [results]);

  /**
   * TODO: Known issue
   * See: https://github.com/TanStack/virtual/issues/1119
   */
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer({
    count: visibleCodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 10,
  });

  if (isPending)
    return (
      <div className="flex w-full justify-center">
        <Spinner />
      </div>
    );

  if (isError || !response) return 'Error!';

  function handleCodeSystemSelect(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedCodeSystem(event.target.value);
  }

  const virtualItems = virtualizer.getVirtualItems();
  const topSpacer = virtualItems[0]?.start ?? 0;
  const bottomSpacer =
    virtualizer.getTotalSize() -
    (virtualItems[virtualItems.length - 1]?.end ?? 0);

  return (
    <div className="flex h-full min-h-0 w-full flex-col">
      <div className="flex flex-col gap-1">
        <CompletenessStatusBadge
          completenessStatus={response.data.completeness_status}
        />
        <h3 className="text-xl font-bold">{defaultCondition} code set</h3>
      </div>

      <div className="border-bottom-[1px] mb-4 flex min-w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
        <Search
          onChange={(e) => debouncedSearchUpdate(e.target.value)}
          id="code-search"
          name="code-search"
          placeholder="Search code set"
        />

        <CodeSystemSelection
          selectedCodeSystem={selectedCodeSystem}
          handleCodeSystemSelect={handleCodeSystemSelect}
          codeSystems={response.data.systems}
        />
      </div>

      <hr className="border-blue-cool-5! mb-6 w-full border" />
      <ConditionCodeGroupingParagraph />

      {isLoadingResults ? (
        <div className="pt-10">
          <p>Loading...</p>
        </div>
      ) : hasSearched && searchText && visibleCodes.length === 0 ? (
        <div className="pt-10">
          <p>No codes match the search criteria.</p>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="h-100 overflow-y-auto sm:h-full"
          tabIndex={0}
        >
          <div
            role="table"
            aria-label={`Codes in set with ID ${conditionId}`}
            className="grid grid-cols-[1fr_1fr_4fr]"
          >
            <div role="rowgroup" className="contents">
              <div role="row" className="contents">
                <Header>Code</Header>
                <Header>Code system</Header>
                <Header>Condition</Header>
              </div>
            </div>

            <div role="rowgroup" className="contents">
              <div
                className="col-span-full"
                style={{ height: `${topSpacer}px` }}
              />

              {virtualItems.map((virtualRow) => {
                const code = visibleCodes[virtualRow.index];
                const matchingResult = resultsByCode.get(
                  `${code.system}-${code.code}-${code.description}`
                );
                return (
                  <div
                    key={`${code.system}-${code.code}-${virtualRow.index}`}
                    role="row"
                    className="contents"
                  >
                    <div role="cell" className="pb-6">
                      {highlightMatches(
                        code.code,
                        matchingResult?.matches,
                        'code'
                      )}
                    </div>
                    <div role="cell" className="text-gray-cool-60 pb-6">
                      {code.system}
                    </div>
                    <div role="cell" className="pb-6">
                      {highlightMatches(
                        code.description,
                        matchingResult?.matches,
                        'description'
                      )}
                    </div>
                  </div>
                );
              })}

              <div
                className="col-span-full"
                style={{ height: `${bottomSpacer}px` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Header({ children }: { children: React.ReactNode }) {
  return (
    <div
      role="columnheader"
      className="sticky top-0 z-10 h-10 bg-white pb-2 text-left font-semibold"
    >
      {children}
    </div>
  );
}

type CodeSystemSelectionProps = {
  selectedCodeSystem: string;
  handleCodeSystemSelect: (
    event: React.ChangeEvent<HTMLSelectElement, Element>
  ) => void;
  codeSystems: CodeSystemsReponse[];
};

function CodeSystemSelection({
  selectedCodeSystem,
  handleCodeSystemSelect,
  codeSystems,
}: CodeSystemSelectionProps) {
  return (
    <SelectContainer className="max-w-3xs!">
      <Field>
        <Label>Code system</Label>
        <Select value={selectedCodeSystem} onChange={handleCodeSystemSelect}>
          <option key="all-code-systems" value="all">
            All code systems
          </option>
          {codeSystems.map((s) => (
            <option key={s.id} value={s.key}>
              {s.display_name}
            </option>
          ))}
        </Select>
      </Field>
    </SelectContainer>
  );
}

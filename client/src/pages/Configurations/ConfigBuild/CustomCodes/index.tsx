import { CodeSystem } from '../../../../api/schemas/codeSystem';
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
import { DbConfigurationCustomCode } from '../../../../api/schemas';
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
  disabled: boolean;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function CustomCodesDetail({
  configurationId,
  customCodes,
  disabled,
  isOpen,
  setIsOpen,
}: CustomCodesDetailProps) {
  const { mutate: deleteCode } = useDeleteCustomCodeFromConfiguration();
  const [selectedCustomCode, setSelectedCustomCode] =
    useState<DbConfigurationCustomCode | null>(null);
  const queryClient = useQueryClient();
  const showToast = useToast();

  const resetModal = () => {
    setSelectedCustomCode(null);
  };

  return (
    <div role="region">
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
    <p>
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
        <SelectContainer className="max-w-3xs!">
          <Field>
            <Label>Code system</Label>
            <Select
              value={selectedCodeSystem}
              onChange={handleCodeSystemSelect}
            >
              <option key="all-code-systems" value="all">
                All code systems
              </option>
              {Object.keys(CodeSystem).map((system) => (
                <option key={system} value={system}>
                  {system}
                </option>
              ))}
            </Select>
          </Field>
        </SelectContainer>
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
        <div ref={parentRef} className="h-full overflow-y-auto">
          <div
            role="table"
            id="codeset-table"
            aria-label={`Codes in set with ID ${conditionId}`}
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 4fr' }}
          >
            <div role="rowgroup" style={{ display: 'contents' }}>
              <div role="row" style={{ display: 'contents' }}>
                <div
                  role="columnheader"
                  className="sticky top-0 z-10 h-10 bg-white pb-2 text-left font-semibold"
                >
                  Code
                </div>
                <div
                  role="columnheader"
                  className="sticky top-0 z-10 h-10 bg-white pb-2 text-left font-semibold"
                >
                  Code system
                </div>
                <div
                  role="columnheader"
                  className="sticky top-0 z-10 h-10 bg-white pb-2 text-left font-semibold"
                >
                  Condition
                </div>
              </div>
            </div>

            <div role="rowgroup" style={{ display: 'contents' }}>
              <div style={{ height: `${topSpacer}px`, gridColumn: '1 / -1' }} />

              {virtualItems.map((virtualRow) => {
                const code = visibleCodes[virtualRow.index];
                const matchingResult = results.find(
                  (r) =>
                    r.item.code === code.code &&
                    r.item.description === code.description
                );
                return (
                  <div
                    key={`${code.system}-${code.code}-${virtualRow.index}`}
                    role="row"
                    style={{ display: 'contents' }}
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
                style={{ height: `${bottomSpacer}px`, gridColumn: '1 / -1' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

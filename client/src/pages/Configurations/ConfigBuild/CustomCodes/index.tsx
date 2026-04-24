import { CodeSystem } from '../../../../api/schemas/codeSystem';
import { Search } from '@components/Search';
import { Label, Select } from '@trussworks/react-uswds';
import { useSearch } from '../../../../hooks/useSearch';
import { useGetCondition } from '../../../../api/conditions/conditions';
import { useDebouncedCallback } from 'use-debounce';
import type { FuseResultMatch } from 'fuse.js';
import { highlightMatches } from '../../../../utils';
import { TesLink } from '../../TesLink';
import { useQueryClient } from '@tanstack/react-query';
import { useState, useMemo } from 'react';
import {
  useDeleteCustomCodeFromConfiguration,
  getGetConfigurationQueryKey,
} from '../../../../api/configurations/configurations';
import { DbConfigurationCustomCode } from '../../../../api/schemas';
import { Spinner } from '@components/Spinner';
import { useToast } from '../../../../hooks/useToast';
import { Button } from '@components/Button';
import { CustomCodeModal } from './CustomCodeModal';

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

    // Treat inputs like 123, A12, J10, Z21.3 as code-like
    // and avoid fuzzy matching them too loosely.
    return (
      /^[a-z0-9.-]+$/i.test(trimmed) &&
      !trimmed.includes(' ') &&
      !/[a-z]{2}/i.test(trimmed)
    );
  }

  const visibleCodes = useMemo(() => {
    const trimmedSearch = searchText.trim();

    if (!trimmedSearch) {
      return filteredCodes;
    }

    // For code-like input, do exact/prefix matching on code only
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

    // For regular text input, keep existing Fuse behavior
    return results.map((r) => r.item);
  }, [filteredCodes, results, searchText]);

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
            {Object.keys(CodeSystem).map((system) => (
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
      ) : hasSearched && searchText && visibleCodes.length === 0 ? (
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
            <thead className="bg-opacity-100 sticky -top-6 h-10 bg-white text-left">
              <tr>
                <th>Code</th>
                <th>Code system</th>
                <th>Condition</th>
              </tr>
            </thead>
            <tbody>
              {visibleCodes.map((code) => {
                const matchingResult = results.find(
                  (r) =>
                    r.item.code === code.code &&
                    r.item.description === code.description
                );

                return (
                  <ConditionCodeRow
                    key={`${code.system}-${code.code}`}
                    codeSystem={code.system}
                    code={code.code}
                    text={code.description}
                    matches={matchingResult?.matches}
                  />
                );
              })}
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
      <td className="w-1/6 pb-6">{highlightMatches(code, matches, 'code')}</td>
      <td className="text-gray-cool-60 w-1/6 pb-6">{codeSystem}</td>
      <td className="w-4/6 pb-6">
        {highlightMatches(text, matches, 'description')}
      </td>
    </tr>
  );
}

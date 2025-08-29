import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useEffect, useMemo, useState } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import { Icon, Label, Select } from '@trussworks/react-uswds';
import { useSearch } from '../../../hooks/useSearch';
import AddConditionCodeSetsDrawer from '../../../components/Drawer/AddConditionCodeSets';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useGetCondition } from '../../../api/conditions/conditions';
import { useDebouncedCallback } from 'use-debounce';
import { FuseResultMatch } from 'fuse.js';

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
  if (isError) return 'Error!';

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
        <Builder code_sets={response.data.code_sets} />
      </SectionContainer>
    </div>
  );
}

type BuilderProps = Pick<GetConfigurationResponse, 'code_sets'>;

function Builder({ code_sets }: BuilderProps) {
  const [selectedCodesetId, setSelectedCodesetId] = useState<string | null>(
    null
  );

  function onClick(id: string) {
    setSelectedCodesetId(id);
  }

  function toggleDrawer() {
    setDrawerActive(!drawerActive);
  }

  function onSearch(/* filter: string */) {}
  // function onSave() {}
  function onClose() {
    setDrawerActive(false);
  }

  const [drawerActive, setDrawerActive] = useState(false);

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
              onClick={toggleDrawer}
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
                    onClick={() => onClick(codeSet.condition_id)}
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
        </div>
        <div className="flex max-h-[34.5rem] flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          <DefaultGroupingParagraph />
          {selectedCodesetId ? (
            <ConditionCodeTable conditionId={selectedCodesetId} />
          ) : null}
        </div>
      </div>
      <AddConditionCodeSetsDrawer
        isOpen={drawerActive}
        onClose={onClose}
        onSearch={onSearch}
      />
    </div>
  );
}

function DefaultGroupingParagraph() {
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
        <div>
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

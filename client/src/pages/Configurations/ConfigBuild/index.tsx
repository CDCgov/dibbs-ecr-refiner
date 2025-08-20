import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useMemo, useState } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import { Icon, Label, Select } from '@trussworks/react-uswds';
import { useSearch } from '../../../hooks/useSearch';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useGetCondition } from '../../../api/conditions/conditions';

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
  const { data: response, isLoading, isError } = useGetCondition(conditionId);
  const [selectedCodeSystem, setSelectedCodeSystem] = useState<string>('all');

  const codes = useMemo(
    () => response?.data.codes ?? [],
    [response?.data.codes]
  );

  const filteredCodes = useMemo(() => {
    return selectedCodeSystem === 'all'
      ? codes
      : codes.filter((code) => code.system === selectedCodeSystem);
  }, [codes, selectedCodeSystem]);

  const { searchText, setSearchText, results } = useSearch(
    filteredCodes,
    {
      keys: [
        { name: 'code', weight: 0.7 },
        { name: 'description', weight: 0.3 },
      ],
      minMatchCharLength: 3,
    },
    300
  );

  // Decide which data to display
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
          onChange={(e) => setSearchText(e.target.value)}
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
      {visibleCodes.length ? (
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
              {visibleCodes.map((code) => (
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
      ) : (
        <div className="pt-10">
          <p>No codes match the search criteria.</p>
        </div>
      )}
    </div>
  );
}

interface ConditionCodeRowProps {
  code: string;
  codeSystem: string;
  text: string;
}

function ConditionCodeRow({ code, codeSystem, text }: ConditionCodeRowProps) {
  return (
    <tr>
      <td className="w-1/6">{code}</td>
      <td className="w-1/6"> {codeSystem}</td>
      <td className="w-4/6">{text}</td>
    </tr>
  );
}

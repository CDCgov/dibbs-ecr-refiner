import { useParams } from 'react-router';
import NotFound from '../../NotFound';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useState } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import { Icon, Label, Select } from '@trussworks/react-uswds';
import { useSearch } from '../../../hooks/useSearch';

export default function ConfigBuild() {
  // Fetch config by ID on page load for each of these steps
  // build -> test -> activate
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <TitleContainer>
        <Title>Condition name</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={id} />
          <Button to={`/configurations/${id}/test`}>
            Next: Test configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <Builder />
      </SectionContainer>
    </div>
  );
}

const builderRequest = {
  allCodeSystems: [
    {
      id: 'loinc-id',
      name: 'LOINC',
    },
    {
      id: 'snomed-id',
      name: 'SNOMED',
    },
  ],
  codeSets: [
    {
      id: 'covid-19-id',
      display_name: 'COVID-19',
      code_count: 9,
      codes: [
        {
          code: '45068-2',
          codeSystem: 'SNOMED',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-3',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-4',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-1',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-5',
          codeSystem: 'SNOMED',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-6',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-7',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-8',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
        {
          code: '45068-9',
          codeSystem: 'LOINC',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
        },
      ],
    },
    {
      id: 'chlamydia-id',
      display_name: 'Chlamydia',
      code_count: 2,
      codes: [
        {
          code: '45076-7',
          codeSystem: 'SNOMED',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Genital specimen by NAA with probe detection',
        },
        {
          code: '45076-8',
          codeSystem: 'SNOMED',
          text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Genital specimen by NAA with probe detection',
        },
      ],
    },
    {
      id: 'gonorrhea-id',
      display_name: 'Gonorrhea',
      code_count: 3,
      codes: [
        {
          code: '5028-6',
          codeSystem: 'LOINC',
          text: 'Neisseria gonorrhoeae rRNA [Presence] in Specimen by Probe',
        },
        {
          code: '10001-7',
          codeSystem: 'SNOMED',
          text: 'Neisseria gonorrhoeae rRNA [Presence] in Specimen by Probe',
        },
        {
          code: '2101-0',
          codeSystem: 'LOINC',
          text: 'Neisseria gonorrhoeae rRNA [Presence] in Specimen by Probe',
        },
      ],
    },
  ],
};

function Builder() {
  const [selectedCodesetId, setSelectedCodesetId] = useState<string | null>(
    null
  );
  const [selectedCodeSystem, setSelectedCodeSystem] = useState<string>('all');

  // NOTE: this won't work in prod since there are so many codes.
  // We'll need to load only the codes from the condition codeset being observed.
  const allCodes = builderRequest.codeSets.flatMap((codeSet) =>
    codeSet.codes.map((code) => ({
      ...code,
      codeSetId: codeSet.id,
      codeSetName: codeSet.display_name,
    }))
  );

  const filteredCodes = allCodes.filter((code) => {
    const matchesCodeset =
      !selectedCodesetId || code.codeSetId === selectedCodesetId;
    const matchesCodeSystem =
      selectedCodeSystem === 'all' || code.codeSystem === selectedCodeSystem;
    return matchesCodeset && matchesCodeSystem;
  });

  const { searchText, setSearchText, results } = useSearch(filteredCodes, {
    keys: [
      { name: 'code', weight: 0.7 },
      { name: 'text', weight: 0.3 },
    ],
    includeScore: true,
  });

  function onClick(id: string) {
    setSelectedCodesetId(id);
  }

  function handleCodeSystemSelect(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedCodeSystem(event.target.value);
  }

  // Decide which data to display
  const visibleCodes = searchText ? results.map((r) => r.item) : filteredCodes;

  return (
    <div className="bg-blue-cool-5 h-[35rem] rounded-lg p-2">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col gap-4 py-4 sm:w-1/3 md:px-2">
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <label className="font-bold text-[#919191]" htmlFor="open-codesets">
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
          <ul className="flex flex-col gap-2">
            {builderRequest.codeSets.map((codeSet) => (
              <li key={codeSet.id}>
                <button
                  className={classNames(
                    'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                    {
                      'bg-white': selectedCodesetId === codeSet.id,
                    }
                  )}
                  onClick={() => onClick(codeSet.id)}
                >
                  <span>{codeSet.display_name}</span>
                  <span>{codeSet.code_count}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex max-h-[34.5rem] flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          <div className="border-bottom-[1px] mb-4 flex w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
            <Search
              onChange={(e) => setSearchText(e.target.value)}
              id="code-search"
              name="code-search"
              type="search"
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
                {builderRequest.allCodeSystems.map((cs) => (
                  <option key={`${cs.id}-${cs.name}`} value={cs.name}>
                    {cs.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <hr className="border-blue-cool-5 w-full border-[1px]" />
          <p>
            These condition code sets come from the default groupings in the{' '}
            <a
              className="text-blue-cool-60 hover:underline"
              href="https://tes.tools.aimsplatform.org/auth/signin"
              target="_blank"
              rel="noopener"
            >
              TES (Terminology Exchange Service).
            </a>
          </p>
          {selectedCodesetId ? (
            <table className="w-full border-separate border-spacing-y-4">
              <thead className="sr-only">
                <tr>
                  <th>Code</th>
                  <th>Code system</th>
                  <th>Condition</th>
                </tr>
              </thead>
              <tbody>
                {visibleCodes.flatMap((code) => (
                  <ConditionCodeRow
                    key={`${code.codeSetId}-${code.code}`}
                    codeSystem={code.codeSystem}
                    code={code.code}
                    text={code.text}
                  />
                ))}
              </tbody>
            </table>
          ) : null}
        </div>
      </div>
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

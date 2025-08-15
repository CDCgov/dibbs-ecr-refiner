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
import { useRef, useState } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import {
  ComboBox,
  ComboBoxRef,
  Form,
  Icon,
  Label,
  Modal,
  ModalFooter,
  ModalHeading,
  ModalRef,
  ModalToggleButton,
  Select,
} from '@trussworks/react-uswds';
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

const builderResponse = {
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
      id: 'hiv-id',
      display_name: 'Human immunodeficiency virus infection (HIV)',
      code_count: 7,
      codes: [
        {
          code: '45568-4',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45569-1',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45570-5',
          codeSystem: 'SNOMED',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45571-6',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45572-7',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45573-8',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
        },
        {
          code: '45574-9',
          codeSystem: 'LOINC',
          text: 'Human immunodeficiency virus infection (HIV) DNA [Presence] in Specimen by Probe',
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
  const allCodes = builderResponse.codeSets.flatMap((codeSet) =>
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

  // const modalRef = useRef<ModalRef>(null);
  // const listRef = useRef<ComboBoxRef>(null);
  const conditionData = {
    // TODO: Figure out what this data should look like and require using real
    // UUIDs since keys need to be unique.
    '3d7fb83d-d664-4b82-a0fb-3f8decd307cc': 'Anaplasmosis',
    '1be0a722-ead6-4a54-ad90-e83c139ceb3c': 'Chlamydia trachomatis infection',
    '0c157c35-b9a2-431f-badc-9ee0ea12003f': 'Gonorrhea',
    'f0365ece-3ec7-486a-ba73-7f5d1de64ca8': 'HIV',
    '985fc9f8-86dc-4e12-95f1-b7457b3497ca': 'Syphilis',
    '6d541ced-f53b-4690-9eca-9186b5aa654c':
      'Human immunodeficiency virus (HIV)',
    'f68575c8-7a42-4dda-9505-94a7436f8461': 'Anthrax',
    '890c3126-59a1-48f6-8151-0787f8d8d280': 'Arboviral disease',
    'c2e983af-7ce2-4416-9576-d5b90d9f34de': 'Brucellosis',
    '44fd0471-5e1c-46f9-87f6-b5a797206e3f': 'Campylobacteriosis',
    '27aeaf8e-1d5e-4468-80c6-a73d154ab0c5': 'Cholera',
    '87835fb2-ebac-4052-b627-0150603f55e3': 'Cocciodioidomycosis',
    'a2b62d15-3edc-4be6-8fd7-6fb0384f8903': 'COVID-19',
    '583f3870-babe-4253-a3b3-d2e6064588bd': 'Cryptosporidiosis',
    '5f2c8e40-1b17-4540-bc8a-5d1fd5d092fa': 'Candida auris',
  };

  const conditionList = Object.entries(conditionData).map(([id, name]) => ({
    value: id,
    label: name,
  }));

  // const [formValid, setFormValid] = useState<boolean>(false);

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
              {builderResponse.codeSets.map((codeSet) => (
                <li key={codeSet.id}>
                  <button
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': selectedCodesetId === codeSet.id,
                      }
                    )}
                    onClick={() => onClick(codeSet.id)}
                    aria-controls={
                      selectedCodesetId ? 'codeset-table' : undefined
                    }
                    aria-pressed={selectedCodesetId === codeSet.id}
                  >
                    <span>{codeSet.display_name}</span>
                    <span>{codeSet.code_count}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="flex max-h-[34.5rem] flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          <div className="border-bottom-[1px] mb-4 flex w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
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
                {builderResponse.allCodeSystems.map((cs) => (
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
              className="text-blue-cool-60 hover:text-blue-cool-50 underline"
              href="https://tes.tools.aimsplatform.org/auth/signin"
              target="_blank"
              rel="noopener"
            >
              TES (Terminology Exchange Service).
            </a>
          </p>
          {selectedCodesetId ? (
            <div role="region">
              <table
                id="codeset-table"
                className="w-full border-separate border-spacing-y-4"
                aria-label={`Codes in set with ID ${selectedCodesetId}`}
              >
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
            </div>
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

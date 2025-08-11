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

function Builder() {
  const [selected, setSelected] = useState<string | null>(null);

  const codeSets = ['COVID-19', 'Chlamydia', 'Gonorrhea'];
  const conditionCodes = [
    {
      codeSet: 'COVID-19',
      code: '45068-1',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-2',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-3',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-4',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-5',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-6',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-7',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-8',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'COVID-19',
      code: '45068-9',
      codeSystem: 'LOINC',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Cervix by NAA with probe detection',
    },
    {
      codeSet: 'Gonorrhea',
      code: '5028-6',
      codeSystem: 'LOINC',
      text: 'Neisseria gonorrhoeae rRNA [Presence] in Specimen by Probe',
    },
    {
      codeSet: 'Chlamydia',
      code: '45076-7',
      codeSystem: 'SNOMED',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Genital specimen by NAA with probe detection',
    },
    {
      codeSet: 'Chlamydia',
      code: '45076-8',
      codeSystem: 'SNOMED',
      text: 'Chlamydia trachomatis+Neisseria gonorrhoeae DNA [Presence] in Genital specimen by NAA with probe detection',
    },
  ];

  function onClick(id: string) {
    if (id) {
      setSelected(id);
    }
  }

  return (
    <div className="bg-blue-cool-5 h-[35rem] rounded-lg p-2">
      <div className="flex h-full flex-row gap-4">
        <div className="flex w-1/3 flex-col gap-4 px-2 py-4">
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <label className="font-bold text-[#919191]" htmlFor="open-codesets">
              CONDITION CODE SETS
            </label>
            <button
              className="text-blue-cool-60 font-bold hover:cursor-pointer"
              id="open-codesets"
            >
              + ADD
            </button>
          </div>
          <ul className="flex flex-col gap-2">
            {codeSets.map((codeSet) => (
              <li key={codeSet}>
                <button
                  className={classNames(
                    'h-full w-full rounded p-4 text-left hover:cursor-pointer hover:bg-stone-50',
                    {
                      'bg-white': selected === codeSet,
                    }
                  )}
                  onClick={() => onClick(codeSet)}
                >
                  {codeSet}
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex max-h-[34.5rem] w-2/3 flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-6">
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
          {selected ? (
            <table className="w-full border-separate border-spacing-y-4">
              <thead className="sr-only">
                <tr>
                  <th>Code</th>
                  <th>Code system</th>
                  <th>Condition</th>
                </tr>
              </thead>
              <tbody>
                {conditionCodes
                  .filter((cc) => cc.codeSet === selected)
                  .map((cc) => (
                    <ConditionCodeRow
                      key={`${cc.codeSystem}-${cc.code}`}
                      codeSystem={cc.codeSystem}
                      code={cc.code}
                      text={cc.text}
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

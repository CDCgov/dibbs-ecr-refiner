import { useParams } from 'react-router';
import { Header, SectionContainer } from '../layout';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { Spinner } from '@components/Spinner';
import { GetConfigurationResponse } from '../../../api/schemas';
import { ActivationButtons } from './ActivationButtons';
import { useConfigLockRelease } from '../../../hooks/useConfigLockRelease';

export function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  // release lock on beforeunload
  useConfigLockRelease(id);

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <ConfigurationTitleBar
          title="Turn on configuration"
          subtitle={
            <span>
              Refiner will <span className="font-bold">immediately</span> start
              to refine eCRs with {configuration.data.display_name} as a
              reportable condition, in accordance with this configuration.
            </span>
          }
        />
        <div className="max-w[80rem] mb-8 bg-white p-6">
          <div className="mb-6">
            <ul className="list-none">
              <li>
                <strong>Input: </strong>
                {`eCRs from RCKMS with ${configuration.data.display_name} as a reportable condition`}
              </li>
              <li>
                <strong>Output:</strong> Original + Refined eCR (in XML and HTML
                formats)
              </li>
              <li>
                <strong>Retained data:</strong>{' '}
                {buildRetainedDataDisplay(configuration.data)}
              </li>
            </ul>
          </div>
          <hr className="text-gray-cool-20!" />
          <div className="mt-6">
            <ActivationButtons configurationData={configuration.data} />
          </div>
        </div>
      </SectionContainer>
    </div>
  );
}

function buildRetainedDataDisplay(configurationData: GetConfigurationResponse) {
  const codeSetNames = configurationData.code_sets
    .map((c) => c.display_name)
    .join(', ');

  const customCodeCount = configurationData.custom_codes.codes.length;

  let result = `${codeSetNames} code set(s)`;

  if (customCodeCount > 0) {
    result += `, ${customCodeCount} custom code(s)`;
  }
  return result;
}

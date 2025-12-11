import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { Spinner } from '../../../components/Spinner';
import { VersionMenu } from '../ConfigBuild/VersionMenu';
import { Status } from '../ConfigBuild/Status';
import { GetConfigurationResponse } from '../../../api/schemas';
import { ActivationButtons } from './ActivationButtons';

export function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div>
      <TitleContainer>
        <Title>{configuration.data.display_name}</Title>
        <Status version={configuration.data.active_version} />
      </TitleContainer>
      <NavigationContainer>
        <VersionMenu
          id={configuration.data.id}
          currentVersion={configuration.data.version}
          status={configuration.data.status}
          versions={configuration.data.all_versions}
          step="activate"
        />
        <StepsContainer>
          <Steps configurationId={id} />
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <ConfigurationTitleBar
          step="activate"
          condition={configuration.data.display_name}
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
            <ActivationButtons
              configurationData={configuration.data}
            ></ActivationButtons>
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

  const customCodeCount = configurationData.custom_codes.length;

  let result = `${codeSetNames} code set(s)`;

  if (customCodeCount > 0) {
    result += `, ${customCodeCount} custom code(s)`;
  }
  return result;
}

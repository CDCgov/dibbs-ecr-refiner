import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import {
  getGetConfigurationQueryKey,
  useActivateConfiguration,
  useDeactivateConfiguration,
  useGetConfiguration,
} from '../../../api/configurations/configurations';
import { Spinner } from '../../../components/Spinner';
import { ErrorFallback } from '../../ErrorFallback';
import { VersionMenu } from '../ConfigBuild/VersionMenu';
import { Status } from '../ConfigBuild/Status';
import { useToast } from '../../../hooks/useToast';
import { GetConfigurationResponse } from '../../../api/schemas';
import { ActivationButtons } from './ActivationButtons';
import { QueryClient, useQueryClient } from '@tanstack/react-query';

export function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  const {
    data: configuration,
    isPending,
    isError,
    isSuccess,
    error,
  } = useGetConfiguration(id ?? '');
  const showToast = useToast();

  const { mutate: activate } = useActivateConfiguration();
  const { mutate: deactivate } = useDeactivateConfiguration();

  const queryClient = useQueryClient();

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return <ErrorFallback error={error} />;

  function handleActivation() {
    if (!configuration || !configuration.data) {
      showToast({
        variant: 'error',
        heading: 'Something went wrong',
        body: 'Condition not defined',
      });
      return;
    }
    activate(
      {
        configurationId: configuration.data.id,
        params: {
          canonical_url: configuration.data.canonical_url,
        },
      },
      {
        onSuccess: async () => {
          await refetchConfigurations(configuration.data, queryClient);

          showToast({
            heading: 'Configuration activated',
            body: '',
          });
        },
      }
    );
  }

  function handleDeactivation() {
    if (!configuration) {
      showToast({
        variant: 'error',
        heading: 'Something went wrong',
        body: 'Condition could not be deactivated',
      });
      return;
    }

    // in any case where we need to deactivate, we need the active
    // config ID. Sometimes that's different than the current one, so grab it
    // from all_versions
    const idToDeactivate = configuration?.data?.all_versions
      .filter((v) => v.status === 'active')
      .map((c) => c.id);

    deactivate(
      { configurationId: idToDeactivate[0] },
      {
        onSuccess: async () => {
          await refetchConfigurations(configuration.data, queryClient);

          showToast({
            heading: 'Configuration deactivated',
            body: '',
          });
        },
      }
    );
  }

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
          <ActivationButtons
            configurationData={configuration.data}
            isSuccess={isSuccess}
            handleActivation={handleActivation}
            handleDeactivation={handleDeactivation}
            curVersion={configuration.data.version}
            activeVersion={configuration.data.active_version}
          ></ActivationButtons>
        </div>
      </SectionContainer>
    </div>
  );
}

function buildRetainedDataDisplay(configurationData: GetConfigurationResponse) {
  let codeSetDisplay = configurationData.code_sets
    .map((c) => {
      return `${c.display_name}`;
    })
    .join(', ');

  // split out the last trailing comma
  codeSetDisplay = `${codeSetDisplay.slice(0, codeSetDisplay.length)} code set(s)`;

  const numCustomCodes = configurationData.custom_codes.length;
  if (configurationData.custom_codes.length > 0) {
    codeSetDisplay += `, ${numCustomCodes} custom code(s)`;
  }

  return codeSetDisplay;
}

async function refetchConfigurations(
  configurationData: GetConfigurationResponse,
  queryClient: QueryClient
) {
  await Promise.allSettled(
    configurationData.all_versions.map(async (v) => {
      await queryClient.invalidateQueries({
        queryKey: getGetConfigurationQueryKey(v.id),
      });

      await queryClient.refetchQueries({
        queryKey: getGetConfigurationQueryKey(v.id),
      });
    })
  );
}

import { GetConfigurationResponse } from '../../../api/schemas';
import { SwitchFromPrevious } from './buttonDisplays/SwitchFromPreviousButtons';
import { TurnOffButtons } from './buttonDisplays/TurnOffButtons';
import { TurnOnButtons } from './buttonDisplays/TurnOnButtons';
import { useQueryClient, QueryClient } from '@tanstack/react-query';
import {
  useActivateConfiguration,
  useDeactivateConfiguration,
  getGetConfigurationQueryKey,
} from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';

interface ActivationButtonsProps {
  configurationData: GetConfigurationResponse;
}

export function ActivationButtons({
  configurationData,
}: ActivationButtonsProps) {
  const queryClient = useQueryClient();

  const { mutate: activate } = useActivateConfiguration();
  const { mutate: deactivate } = useDeactivateConfiguration();

  const showToast = useToast();

  function handleActivation() {
    if (!configurationData) {
      showToast({
        variant: 'error',
        heading: 'Something went wrong',
        body: 'Condition not defined',
      });
      return;
    }
    activate(
      {
        configurationId: configurationData.id,
      },
      {
        onSuccess: async () => {
          await refetchConfigurations(configurationData, queryClient);

          showToast({
            heading: 'Configuration activated',
            body: '',
          });
        },
      }
    );
  }

  function handleDeactivation() {
    if (!configurationData || !configurationData.active_configuration_id) {
      showToast({
        variant: 'error',
        heading: 'Something went wrong',
        body: 'Condition could not be deactivated',
      });
      return;
    }

    deactivate(
      { configurationId: configurationData.active_configuration_id },
      {
        onSuccess: async () => {
          await refetchConfigurations(configurationData, queryClient);

          showToast({
            heading: 'Configuration deactivated',
            body: '',
          });
        },
      }
    );
  }

  const curVersion = configurationData.version;
  const activeVersion = configurationData.active_version;

  if (activeVersion === null) {
    return <TurnOnButtons handleActivation={handleActivation}></TurnOnButtons>;
  } else if (curVersion === activeVersion) {
    return <TurnOffButtons handleDeactivation={handleDeactivation} />;
  }

  return (
    <SwitchFromPrevious
      handleActivation={handleActivation}
      handleDeactivation={handleDeactivation}
      curVersion={curVersion}
      activeVersion={activeVersion}
    />
  );
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

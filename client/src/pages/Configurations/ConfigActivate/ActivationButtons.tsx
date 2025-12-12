import { GetConfigurationResponse } from '../../../api/schemas';
import { SwitchFromPrevious } from './buttonDisplays/SwitchFromPreviousButtons';
import { TurnOffButtons } from './buttonDisplays/TurnOffButtons';
import { TurnOnButtons } from './buttonDisplays/TurnOnButtons';
import { useQueryClient } from '@tanstack/react-query';
import {
  useActivateConfiguration,
  useDeactivateConfiguration,
  getGetConfigurationQueryKey,
} from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';

interface ActivationButtonsProps {
  configurationData: GetConfigurationResponse;
}

export function ActivationButtons({
  configurationData,
}: ActivationButtonsProps) {
  const queryClient = useQueryClient();

  const { mutate: activate } = useActivateConfiguration();
  const { mutate: deactivate } = useDeactivateConfiguration();
  const formatError = useApiErrorFormatter();

  const showToast = useToast();

  function handleActivation() {
    activate(
      {
        configurationId: configurationData.id,
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationData.id),
          });

          showToast({
            heading: 'Configuration activated',
            body: '',
          });
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error associating condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  function handleDeactivation() {
    if (!configurationData.active_configuration_id) {
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
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationData.id),
          });

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

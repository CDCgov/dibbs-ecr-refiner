import { GetConfigurationResponse } from '../../../api/schemas';
import { TurnOnConfigButton } from './TurnOnConfigButton';
import { useQueryClient } from '@tanstack/react-query';
import {
  useActivateConfiguration,
  useDeactivateConfiguration,
  getGetConfigurationQueryKey,
} from '../../../api/configurations/configurations';
import { useToast } from '../../../hooks/useToast';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { TurnOffConfigButton } from './TurnOffConfigButton';
import { SwitchToVersionButton } from './SwitchToVersionButton';

interface ActivationButtonsProps {
  configurationData: GetConfigurationResponse;
  isLocked?: boolean;
}

export function ActivationButtons({
  configurationData,
  isLocked = false,
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
            heading: 'Error activating condition',
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
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error deactivating condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  const curVersion = configurationData.version;
  const activeVersion = configurationData.active_version;

  if (!activeVersion) {
    return (
      <TurnOnConfigButton
        handleActivation={handleActivation}
        disabled={isLocked}
      />
    );
  }

  if (curVersion === activeVersion) {
    return (
      <TurnOffConfigButton
        handleDeactivation={handleDeactivation}
        disabled={isLocked}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-bold">Option 1</h3>
        <SwitchToVersionButton
          handleActivation={handleActivation}
          activeVersion={activeVersion}
          curVersion={curVersion}
        />
      </div>
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-bold">Option 2</h3>
        <TurnOffConfigButton
          handleDeactivation={handleDeactivation}
          disabled={isLocked}
        />
      </div>
    </div>
  );
}

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
import { AxiosError } from 'axios';
import { useState } from 'react';

interface ActivationButtonsProps {
  configurationData: GetConfigurationResponse;
  isLocked?: boolean;
}

export function ActivationButtons({
  configurationData,
  isLocked = false,
}: ActivationButtonsProps) {
  const queryClient = useQueryClient();

  const { mutateAsync: activate } = useActivateConfiguration();
  const { mutateAsync: deactivate } = useDeactivateConfiguration();

  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  const [isLoading, setIsLoading] = useState(false);

  async function handleActivation() {
    setIsLoading(true);
    try {
      await activate({ configurationId: configurationData.id });
      await queryClient.invalidateQueries({
        queryKey: getGetConfigurationQueryKey(configurationData.id),
      });
      showToast({ heading: 'Configuration activated', body: '' });
    } catch (error) {
      const errorDetail =
        error instanceof AxiosError
          ? formatError(error) || error.message
          : 'Unknown error';
      showToast({
        variant: 'error',
        heading: 'Error activating condition',
        body: errorDetail,
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeactivation() {
    if (!configurationData.active_configuration_id) {
      showToast({
        variant: 'error',
        heading: 'Something went wrong',
        body: 'Condition could not be deactivated',
      });
      return;
    }

    setIsLoading(true);

    try {
      await deactivate({
        configurationId: configurationData.active_configuration_id,
      });
      await queryClient.invalidateQueries({
        queryKey: getGetConfigurationQueryKey(configurationData.id),
      });
      showToast({ heading: 'Configuration deactivated', body: '' });
    } catch (error) {
      const errorDetail =
        error instanceof AxiosError
          ? formatError(error) || error.message
          : 'Unknown error';
      showToast({
        variant: 'error',
        heading: 'Error deactivating condition',
        body: errorDetail,
      });
    } finally {
      setIsLoading(false);
    }
  }

  const curVersion = configurationData.version;
  const activeVersion = configurationData.active_version;

  if (!activeVersion) {
    return (
      <TurnOnConfigButton
        handleActivation={handleActivation}
        disabled={isLocked}
        isLoading={isLoading}
        hasPrimaryCondition={!!configurationData.condition_id}
      />
    );
  }

  if (curVersion === activeVersion) {
    return (
      <TurnOffConfigButton
        handleDeactivation={handleDeactivation}
        disabled={isLocked}
        isLoading={isLoading}
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
          isLoading={isLoading}
          grouped
        />
      </div>
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-bold">Option 2</h3>
        <TurnOffConfigButton
          handleDeactivation={handleDeactivation}
          disabled={isLocked}
          isLoading={isLoading}
          grouped
        />
      </div>
    </div>
  );
}

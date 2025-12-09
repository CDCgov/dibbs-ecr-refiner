import { useEffect, useState } from 'react';
import { GetConfigurationResponse } from '../../../api/schemas';
import { SwitchFromPrevious } from './buttonDisplays/SwitchFromPreviousButtons';
import { TurnOffButtons } from './buttonDisplays/TurnOffButtons';
import { TurnOnButtons } from './buttonDisplays/TurnOnButtons';

enum StatusUpdateStates {
  TURN_ON,
  TURN_OFF,
  SWITCH_FROM_PREVIOUS,
}

interface ActivationButtonsProps {
  configurationData: GetConfigurationResponse;
  isSuccess: boolean;
  handleActivation: () => void;
  handleDeactivation: () => void;
  curVersion: number;
  activeVersion: number | null;
}

export function ActivationButtons({
  configurationData,
  isSuccess,
  handleActivation,
  handleDeactivation,
  curVersion,
  activeVersion,
}: ActivationButtonsProps) {
  const [buttonState, setButtonState] = useState<StatusUpdateStates>();

  useEffect(() => {
    if (!configurationData) return;
    const currentVersionIsActive = configurationData.status === 'active';
    const noCurrentActiveConfig = configurationData.active_version === null;

    if (currentVersionIsActive) {
      setButtonState(StatusUpdateStates.TURN_OFF);
    } else if (noCurrentActiveConfig) {
      setButtonState(StatusUpdateStates.TURN_ON);
    } else {
      setButtonState(StatusUpdateStates.SWITCH_FROM_PREVIOUS);
    }
  }, [isSuccess, configurationData]);

  return (
    <div className="mt-6">
      {buttonState === StatusUpdateStates.SWITCH_FROM_PREVIOUS && (
        <SwitchFromPrevious
          handleActivation={handleActivation}
          handleDeactivation={handleDeactivation}
          curVersion={curVersion}
          activeVersion={activeVersion}
        />
      )}
      {buttonState === StatusUpdateStates.TURN_ON && (
        <TurnOnButtons handleActivation={handleActivation}></TurnOnButtons>
      )}

      {buttonState === StatusUpdateStates.TURN_OFF && (
        <TurnOffButtons handleDeactivation={handleDeactivation} />
      )}
    </div>
  );
}

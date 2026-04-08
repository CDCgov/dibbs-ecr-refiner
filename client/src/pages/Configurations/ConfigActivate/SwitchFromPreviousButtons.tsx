import { SwitchToVersionButton } from './SwitchToVersionButton';
import { TurnOffConfigButton } from './TurnOffConfigButton';

interface SwitchFromPreviousProps {
  handleActivation: () => void;
  handleDeactivation: () => void;
  curVersion: number;
  activeVersion: number | null;
  disabled: boolean;
}
export function SwitchFromPrevious({
  handleActivation,
  handleDeactivation,
  curVersion,
  activeVersion,
  disabled,
}: SwitchFromPreviousProps) {
  return (
    <div>
      <SwitchToVersionButton
        handleActivation={handleActivation}
        activeVersion={activeVersion}
        curVersion={curVersion}
      />
      <TurnOffConfigButton
        handleDeactivation={handleDeactivation}
        disabled={disabled}
      />
    </div>
  );
}

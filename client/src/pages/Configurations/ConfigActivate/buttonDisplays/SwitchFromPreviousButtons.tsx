import { ModalRef } from '@trussworks/react-uswds';
import { SwitchActivationModal } from '../modals/SwitchActivationModal';
import { useRef } from 'react';
import classNames from 'classnames';
import { TurnOffModal } from '../modals/TurnOffModal';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';

interface SwitchFromPreviousProps {
  handleActivation: () => void;
  handleDeactivation: () => void;
  curVersion: number;
  activeVersion: number | null;
  disabled?: boolean;
}
export function SwitchFromPrevious({
  handleActivation,
  handleDeactivation,
  curVersion,
  activeVersion,
  disabled,
}: SwitchFromPreviousProps) {
  const deactivateRef = useRef<ModalRef>(null);
  const activateRef = useRef<ModalRef>(null);

  return (
    <div>
      <h3 className="mb-4 text-lg font-bold">Option 1</h3>
      <div>
        <ModalToggleButton
          modalRef={activateRef}
          opener
          className={classNames('self-start')}
        >
          Switch to version {curVersion}
        </ModalToggleButton>
        <>
          Safely replace the current version with this one — it will begin
          processing immediately
        </>

        <SwitchActivationModal
          curVersion={curVersion}
          activeVersion={activeVersion}
          handleActivation={handleActivation}
          modalRef={activateRef}
        ></SwitchActivationModal>

        <h3 className="mt-6 mb-4 text-lg font-bold">Option 2</h3>
        <ModalToggleButton
          modalRef={deactivateRef}
          opener
          variant="secondary"
          className={classNames('self-start')}
          disabled={disabled}
        >
          Turn off configuration
        </ModalToggleButton>
        <>
          Stop the current version. No version will be active until you turn one
          on
        </>
        <TurnOffModal
          handleDeactivation={handleDeactivation}
          modalRef={deactivateRef}
        ></TurnOffModal>
      </div>
    </div>
  );
}

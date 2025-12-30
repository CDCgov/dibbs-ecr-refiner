import { ModalRef, ModalToggleButton } from '@trussworks/react-uswds';
import { SwitchActivationModal } from '../modals/SwitchActivationModal';
import { useRef } from 'react';
import classNames from 'classnames';
import {
  PRIMARY_BUTTON_STYLES,
  SECONDARY_BUTTON_STYLES,
} from '../../../../components/Button';
import { TurnOffModal } from '../modals/TurnOffModal';

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
          className={classNames('self-start', PRIMARY_BUTTON_STYLES)}
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
          className={classNames('self-start', SECONDARY_BUTTON_STYLES)}
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

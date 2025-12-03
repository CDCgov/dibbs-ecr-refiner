import { RefObject, useEffect, useRef, useState } from 'react';
import { GetConfigurationResponse } from '../../../api/schemas';
import {
  Button,
  PRIMARY_BUTTON_STYLES,
  SECONDARY_BUTTON_STYLES,
} from '../../../components/Button';
import {
  ModalRef,
  Modal,
  ModalHeading,
  ModalFooter,
  ModalToggleButton,
} from '@trussworks/react-uswds';
import classNames from 'classnames';

enum ModalStates {
  TURN_ON,
  TURN_OFF,
  SWITCH_FROM_PREVIOUS,
}

const EMPTY_BUTTON_STATE = {
  activate: false,
  deactivate: false,
  activateText: '',
  deactivateText: '',
  deactivateHelper: '',
  activateHelper: '',
  modalKey: ModalStates.TURN_OFF,
};

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
  const [buttonState, setButtonState] = useState(
    structuredClone(EMPTY_BUTTON_STATE)
  );

  useEffect(() => {
    if (!configurationData) return;
    const newButtonState = structuredClone(EMPTY_BUTTON_STATE);
    const currentVersionIsActive = configurationData.status === 'active';
    const noCurrentActiveConfig = configurationData.active_version === null;

    if (currentVersionIsActive) {
      newButtonState['deactivate'] = true;
      newButtonState['deactivateText'] = 'Turn off configuration';
      newButtonState['modalKey'] = ModalStates.TURN_OFF;
    } else if (noCurrentActiveConfig) {
      newButtonState['activate'] = true;
      newButtonState['activateText'] = 'Turn on configuration';
      newButtonState['modalKey'] = ModalStates.TURN_ON;
    } else {
      newButtonState['activate'] = true;
      newButtonState['activateText'] =
        `Switch to version ${configurationData.version}`;
      newButtonState['deactivate'] = true;
      newButtonState['deactivateText'] = 'Turn off current version';
      newButtonState['activateHelper'] =
        'Safely replace the current version with this one — it will begin processing immediately';
      newButtonState['deactivateHelper'] =
        'Stop the current version. No version will be active until you turn one on';
      newButtonState['modalKey'] = ModalStates.SWITCH_FROM_PREVIOUS;
    }

    setButtonState(newButtonState);
  }, [isSuccess, configurationData]);

  const openRef = useRef<ModalRef>(null);
  const closeRef = useRef<ModalRef>(null);

  return (
    <div className="mt-6">
      {buttonState['modalKey'] === ModalStates.SWITCH_FROM_PREVIOUS && (
        <h3 className="mb-4 text-lg font-bold">Option 1</h3>
      )}
      {buttonState['activate'] && (
        <div>
          <ModalToggleButton
            modalRef={openRef}
            opener
            className={classNames('self-start', PRIMARY_BUTTON_STYLES)}
          >
            {buttonState['activateText']}
          </ModalToggleButton>
          <>{buttonState['activateHelper']}</>

          <ActivationConfirmationModal
            modalRef={openRef}
            handleActivation={handleActivation}
            handleDeactivation={handleDeactivation}
            modalKey={buttonState['modalKey']}
            curVersion={curVersion}
            activeVersion={activeVersion}
          />
        </div>
      )}
      {buttonState['modalKey'] === ModalStates.SWITCH_FROM_PREVIOUS && (
        <h3 className="mt-6 mb-4 text-lg font-bold">Option 2</h3>
      )}
      {buttonState['deactivate'] && (
        <div>
          <ModalToggleButton
            modalRef={closeRef}
            opener
            className={classNames('self-start', SECONDARY_BUTTON_STYLES)}
          >
            {buttonState['deactivateText']}
          </ModalToggleButton>
          <>{buttonState['deactivateHelper']}</>

          <ActivationConfirmationModal
            modalRef={closeRef}
            handleActivation={handleActivation}
            handleDeactivation={handleDeactivation}
            modalKey={ModalStates.TURN_OFF}
            curVersion={curVersion}
            activeVersion={activeVersion}
          />
        </div>
      )}
    </div>
  );
}

interface ActivationConfirmationModalProps {
  modalRef: RefObject<ModalRef | null>;
  handleActivation: () => void;
  handleDeactivation: () => void;
  modalKey: ModalStates;
  curVersion: number;
  activeVersion: number | null;
}
function ActivationConfirmationModal({
  modalRef,
  handleActivation,
  handleDeactivation,
  modalKey,
  curVersion,
  activeVersion,
}: ActivationConfirmationModalProps) {
  const modalContent: {
    [k in ModalStates]: {
      title: string;
      body: React.ReactElement;
      footer: React.ReactElement;
    };
  } = {
    [ModalStates.SWITCH_FROM_PREVIOUS]: {
      title: `Switch to Version ${curVersion}`,
      body: (
        <div>
          <p id="activation-confirmation-modal-text" className="my-6">
            You're about to stop Version {activeVersion} and start Version{' '}
            {curVersion}
          </p>
          <p>
            The eCR pipeline will begin using Version {curVersion}{' '}
            <b>immediately</b>
          </p>
          <p>Do you want to continue?</p>
        </div>
      ),
      footer: (
        <div>
          <ModalToggleButton
            modalRef={modalRef}
            closer
            className={SECONDARY_BUTTON_STYLES}
          >
            Cancel
          </ModalToggleButton>
          <Button onClick={() => handleActivation()}>
            Yes, switch to Version {curVersion}
          </Button>
        </div>
      ),
    },
    [ModalStates.TURN_OFF]: {
      title: `Turn off current version`,
      body: (
        <div>
          <p id="deactivation-confirmation-modal-text" className="my-6">
            You’re about to stop the current version. No versions will be
            running until you turn on a new one. Do you want to continue?
          </p>
        </div>
      ),
      footer: (
        <div>
          <ModalToggleButton
            modalRef={modalRef}
            closer
            className={SECONDARY_BUTTON_STYLES}
          >
            Cancel
          </ModalToggleButton>
          <Button onClick={() => handleDeactivation()}>Yes, turn off</Button>
        </div>
      ),
    },
    [ModalStates.TURN_ON]: {
      title: 'Turn on configuration?',
      body: (
        <div>
          <ul>
            <li>
              Refiner will <span className="text-bold">immediately</span> start
              to refine the eCR's
            </li>
            <li>
              You <span className="text-bold">cannot</span> edit this version
              after you activate it
            </li>
          </ul>
          <p id="activation-confirmation-modal-text" className="my-6">
            Are you sure you want to turn on the configuration?
          </p>
        </div>
      ),
      footer: (
        <Button onClick={() => handleActivation()}>
          Yes, turn on configuration
        </Button>
      ),
    },
  };

  const modalToDesplay = modalContent[modalKey];
  return (
    <Modal
      id="activation-confirmation-modal"
      className="max-w-140! p-10 align-top!"
      ref={modalRef}
      aria-labelledby="activation-confirmation-modal-heading"
      aria-describedby="activation-confirmation-modal-text"
    >
      <ModalHeading id="activation-confirmation-modal-heading">
        <div className="mb-6">{modalToDesplay.title}</div>
      </ModalHeading>
      {modalToDesplay.body}
      <ModalFooter className="flex justify-end">
        {modalToDesplay.footer}
      </ModalFooter>
    </Modal>
  );
}

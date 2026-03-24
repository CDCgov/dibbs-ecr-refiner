import { useQueryClient } from '@tanstack/react-query';
import {
  ModalHeading,
  TextInput,
  ModalFooter,
  ButtonGroup,
  ModalRef,
  Label as USWDSLabel,
  Modal as USWDSModal,
  Icon,
} from '@trussworks/react-uswds';
import { Button } from '../../../../components/Button';
import { useState } from 'react';
import {
  getGetConfigurationQueryKey,
  useAddCustomSection,
  useUpdateSection,
} from '../../../../api/configurations/configurations';
import { ModalToggleButton } from '../../../../components/Button/ModalToggleButton';

interface EditCustomSection {
  name: string;
  currentCode: string;
}

interface ModalProps {
  ref: React.RefObject<ModalRef | null>;
  configurationId: string;
  onClose?: () => void;
  initialSection?: EditCustomSection | null;
}

export function Modal({
  ref,
  configurationId,
  onClose,
  initialSection,
}: ModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initialSection?.name ?? '');
  const [newCode, setNewCode] = useState(initialSection?.currentCode ?? '');
  const [errorText, setErrorText] = useState('');
  const { mutate: addCustomSection } = useAddCustomSection();
  const { mutate: updateCustomSection } = useUpdateSection();

  if (initialSection && !name && !newCode) {
    setName(initialSection.name);
    setNewCode(initialSection.currentCode);
  }

  const reset = () => {
    setName('');
    setNewCode('');
    setErrorText('');
    onClose?.();
  };

  const onSubmit = () => {
    const trimmedName = name.trim();
    const trimmedCode = newCode.trim();

    if (!trimmedName) {
      setErrorText('Name is required.');
      return;
    }

    if (!trimmedCode) {
      setErrorText('Code is required.');
      return;
    }

    if (initialSection) {
      updateCustomSection(
        {
          configurationId,
          data: {
            name: trimmedName,
            new_code: trimmedCode,
            current_code: initialSection.currentCode,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            reset();
            ref.current?.toggleModal();
          },
          onError: () => {
            setErrorText('Unable to update custom section.');
          },
        }
      );

      return;
    }

    addCustomSection(
      {
        configurationId,
        data: {
          code: newCode,
          name,
        },
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });
          reset();
          ref.current?.toggleModal();
        },
        onError: () => {
          setErrorText('Unable to add custom section.');
        },
      }
    );
  };

  return (
    <USWDSModal
      className="max-w-100! rounded-sm"
      isLarge
      ref={ref}
      id="custom-section-modal"
      aria-labelledby="modal-heading"
      aria-describedby="modal-description"
      forceAction
    >
      <div className="flex flex-col items-start gap-5">
        <ModalHeading
          id="modal-heading"
          className="text-bold font-merriweather m-0! mb-6 p-0! text-xl"
        >
          {initialSection ? 'Edit custom section' : 'Add a custom section'}
        </ModalHeading>
        <Button
          aria-label="Close this window"
          onClick={() => {
            reset();
            ref.current?.toggleModal();
          }}
          className="absolute top-4 right-0 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
        >
          <Icon.Close className="h-6! w-6!" aria-hidden />
        </Button>
        <div className="flex w-full flex-col items-start">
          <p id="modal-description" className="sr-only">
            Enter your custom section information and click "Add section".
          </p>
          <div className="flex w-full flex-col gap-3">
            <div>
              <USWDSLabel htmlFor="custom-section-name-input">
                Display name (for this section)
              </USWDSLabel>
              <TextInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                id="custom-section-name-input"
                name="custom-section-name-input"
                type="text"
                autoComplete="off"
              />
            </div>
            <div>
              <USWDSLabel htmlFor="custom-section-code-input">
                LOINC code
              </USWDSLabel>
              <TextInput
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                id="custom-section-code-input"
                name="custom-section-code-input"
                type="text"
                autoComplete="off"
              />
            </div>
            {errorText ? (
              <p className="text-secondary-dark text-sm">{errorText}</p>
            ) : null}
          </div>
        </div>
        <ModalFooter className="m-0!">
          <ButtonGroup>
            <ModalToggleButton modalRef={ref} onClick={onSubmit} closer>
              {initialSection ? 'Update section' : 'Add section'}
            </ModalToggleButton>
            <ModalToggleButton
              onClick={() => {
                reset();
                ref.current?.toggleModal();
              }}
              variant="tertiary"
              modalRef={ref}
              closer
            >
              Cancel
            </ModalToggleButton>
          </ButtonGroup>
        </ModalFooter>
      </div>
    </USWDSModal>
  );
}

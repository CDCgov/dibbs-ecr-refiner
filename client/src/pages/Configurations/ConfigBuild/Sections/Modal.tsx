import { useQueryClient } from '@tanstack/react-query';
import {
  ModalHeading,
  TextInput,
  ModalFooter,
  ButtonGroup,
  ModalRef,
  Label as USWDSLabel,
  Modal as USWDSModal,
} from '@trussworks/react-uswds';
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
  mode: 'add' | 'edit';
  onClose?: () => void;
  initialSection?: EditCustomSection | null;
}

export function Modal({
  ref,
  configurationId,
  mode,
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

  const isEdit = mode === 'edit';

  const clearForm = () => {
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

    if (isEdit && initialSection) {
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
            clearForm();
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
          clearForm();
        },
        onError: () => {
          setErrorText('Unable to add custom section.');
        },
      }
    );
  };

  return (
    <USWDSModal
      className="rounded-sm"
      ref={ref}
      id="custom-section-modal"
      aria-labelledby="modal-heading"
      aria-describedby="modal-description"
    >
      <div className="flex flex-col items-start gap-6 p-5">
        <ModalHeading
          className="font-public-sans! text-2xl!"
          id="modal-heading"
        >
          {isEdit ? 'Edit custom section' : 'Add a custom section'}
        </ModalHeading>
        <div className="flex flex-col items-start">
          <p id="modal-description" className="sr-only">
            Enter your custom section information and click "Add section".
          </p>
          <div className="flex flex-col gap-3">
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
              />
            </div>
            {errorText ? (
              <p className="text-secondary-dark text-sm">{errorText}</p>
            ) : null}
          </div>
        </div>
        <ModalFooter>
          <ButtonGroup>
            <ModalToggleButton modalRef={ref} onClick={onSubmit} closer>
              {isEdit ? 'Update section' : 'Add section'}
            </ModalToggleButton>
            <ModalToggleButton variant="tertiary" modalRef={ref} closer>
              Cancel
            </ModalToggleButton>
          </ButtonGroup>
        </ModalFooter>
      </div>
    </USWDSModal>
  );
}

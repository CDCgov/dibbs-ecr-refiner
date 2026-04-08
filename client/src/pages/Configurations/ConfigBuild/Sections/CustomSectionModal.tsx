import { useQueryClient } from '@tanstack/react-query';
import { Button } from '../../../../components/Button';
import { useMemo, useState } from 'react';
import {
  getGetConfigurationQueryKey,
  useAddCustomSection,
  useUpdateSection,
} from '../../../../api/configurations/configurations';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { useToast } from '../../../../hooks/useToast';
import { TextInput } from '../../../../components/TextInput';
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalBody,
} from '../../../../components/Modal';
import { Field } from '../../../../components/Field';
import { Label } from '../../../../components/Label';

interface EditCustomSection {
  name: string;
  currentCode: string;
}

interface CustomSectionModalProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  configurationId: string;
  onClose: () => void;
  initialSection?: EditCustomSection | null;
}

export function CustomSectionModal({
  isOpen,
  setIsOpen,
  configurationId,
  initialSection,
  onClose,
}: CustomSectionModalProps) {
  // calculate a key to ensure the form is set properly when adding or editing
  const formKey = useMemo(
    () =>
      `${isOpen ? 'open' : 'closed'}-${initialSection?.currentCode ?? 'new'}`,
    [isOpen, initialSection?.currentCode]
  );

  const closeModal = () => {
    onClose();
    setIsOpen(false);
  };

  return (
    <Modal open={isOpen} onClose={closeModal}>
      <ModalHeader>
        <ModalTitle>
          {initialSection ? 'Edit custom section' : 'Add a custom section'}
        </ModalTitle>
      </ModalHeader>
      <ModalBody>
        {isOpen && (
          <ModalForm
            key={formKey}
            configurationId={configurationId}
            initialSection={initialSection}
            closeModal={closeModal}
          />
        )}
      </ModalBody>
    </Modal>
  );
}

interface ModalFormProps extends Pick<
  CustomSectionModalProps,
  'configurationId' | 'initialSection'
> {
  closeModal: () => void;
}

function ModalForm({
  configurationId,
  closeModal,
  initialSection,
}: ModalFormProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initialSection?.name ?? '');
  const [newCode, setNewCode] = useState(initialSection?.currentCode ?? '');
  const [errorText, setErrorText] = useState('');
  const { mutate: addCustomSection } = useAddCustomSection();
  const { mutate: updateCustomSection } = useUpdateSection();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  const isEditing = !!initialSection;

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
            closeModal();
            showToast({
              heading: 'Custom section updated',
              body: trimmedName,
            });
          },
          onError: (error) => {
            setErrorText(
              formatError(error) || 'Unable to edit section. Please try again.'
            );
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
          closeModal();
          showToast({
            heading: 'Custom section created',
            body: trimmedName,
          });
        },
        onError: (error) => {
          setErrorText(
            formatError(error) || 'Unable to add section. Please try again.'
          );
        },
      }
    );
  };

  return (
    <div className="flex flex-col gap-10">
      <div className="flex w-full flex-col items-start">
        <p id="modal-description" className="sr-only">
          Enter your custom section information and click "Add section".
        </p>
        <div className="flex w-full flex-col gap-3">
          <Field className="flex flex-col gap-2">
            <Label>Display name (for this section)</Label>
            <TextInput
              value={name}
              onChange={(e) => setName(e.target.value)}
              type="text"
              autoFocus
            />
          </Field>
          <Field className="flex flex-col gap-2">
            <Label>LOINC code</Label>
            <TextInput
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              type="text"
            />
          </Field>
          {errorText ? (
            <p className="text-secondary-dark text-sm">{errorText}</p>
          ) : null}
        </div>
      </div>
      <div className="flex justify-start gap-2">
        <Button onClick={onSubmit}>
          {isEditing ? 'Update section' : 'Add section'}
        </Button>
        <Button onClick={closeModal} variant="tertiary">
          Cancel
        </Button>
      </div>
    </div>
  );
}

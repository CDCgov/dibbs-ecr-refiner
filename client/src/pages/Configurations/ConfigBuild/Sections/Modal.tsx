import { useQueryClient } from '@tanstack/react-query';
import { Icon } from '@trussworks/react-uswds';
import { Button } from '../../../../components/Button';
import { useState } from 'react';
import {
  getGetConfigurationQueryKey,
  useAddCustomSection,
  useUpdateSection,
} from '../../../../api/configurations/configurations';
import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
  Field,
  Input,
  Label,
} from '@headlessui/react';
import { useApiErrorFormatter } from '../../../../hooks/useErrorFormatter';
import { useToast } from '../../../../hooks/useToast';

interface EditCustomSection {
  name: string;
  currentCode: string;
}

interface ModalProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  configurationId: string;
  onClose: () => void;
  initialSection?: EditCustomSection | null;
}

export function Modal({
  isOpen,
  setIsOpen,
  configurationId,
  initialSection,
}: ModalProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initialSection?.name ?? '');
  const [newCode, setNewCode] = useState(initialSection?.currentCode ?? '');
  const [errorText, setErrorText] = useState('');
  const { mutate: addCustomSection } = useAddCustomSection();
  const { mutate: updateCustomSection } = useUpdateSection();
  const formatError = useApiErrorFormatter();
  const showToast = useToast();

  const isEditing = initialSection ? true : false;

  const resetFormData = () => {
    setName('');
    setNewCode('');
    setErrorText('');
  };

  const toggleModal = () => {
    setIsOpen(!isOpen);
  };

  const closeSuccess = () => {
    resetFormData();
    toggleModal();
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
            closeSuccess();
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
          closeSuccess();
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
    <Dialog open={isOpen} onClose={closeSuccess}>
      <DialogBackdrop className="fixed inset-0 bg-black/60" />
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="bg-base-dark/70 fixed inset-0" aria-hidden="true" />
        <DialogPanel className="border-base-lighter relative z-50 h-94 w-100 rounded-sm border bg-white shadow-lg">
          <div className="px-6 py-4">
            <DialogTitle className="font-merriweather text-gray-90 text-3xl font-bold">
              {isEditing ? 'Edit custom section' : 'Add a custom section'}
            </DialogTitle>
            <Button
              aria-label="Close this window"
              onClick={closeSuccess}
              className="absolute top-4 right-0 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
            >
              <Icon.Close className="h-6! w-6!" aria-hidden />
            </Button>
          </div>
          <div className="px-6 py-5">
            <div className="flex w-full flex-col items-start">
              <p id="modal-description" className="sr-only">
                Enter your custom section information and click "Add section".
              </p>
              <div className="flex w-full flex-col gap-3">
                <Field className="flex flex-col gap-2">
                  <Label>Display name (for this section)</Label>
                  <Input
                    className="p-2 outline -outline-offset-1 outline-gray-600"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    type="text"
                    autoFocus
                  />
                </Field>
                <Field className="flex flex-col gap-2">
                  <Label>LOINC code</Label>
                  <Input
                    className="p-2 outline -outline-offset-1 outline-gray-600"
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
          </div>
          <div className="flex justify-start gap-2 px-6 py-4">
            <Button onClick={onSubmit}>
              {isEditing ? 'Update section' : 'Add section'}
            </Button>
            <Button onClick={closeSuccess} variant="tertiary">
              Cancel
            </Button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}

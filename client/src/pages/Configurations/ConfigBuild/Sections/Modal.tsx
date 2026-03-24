import { useQueryClient } from '@tanstack/react-query';
import { TextInput, Label as USWDSLabel } from '@trussworks/react-uswds';
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
} from '@headlessui/react';

interface EditCustomSection {
  name: string;
  currentCode: string;
}

interface ModalTestProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  configurationId: string;
  onClose: () => void;
  initialSection?: EditCustomSection | null;
}

export function ModalTest({
  isOpen,
  setIsOpen,
  configurationId,
  initialSection,
}: ModalTestProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initialSection?.name ?? '');
  const [newCode, setNewCode] = useState(initialSection?.currentCode ?? '');
  const [errorText, setErrorText] = useState('');
  const { mutate: addCustomSection } = useAddCustomSection();
  const { mutate: updateCustomSection } = useUpdateSection();

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
          closeSuccess();
        },
        onError: () => {
          setErrorText('Unable to add custom section.');
        },
      }
    );
  };

  return (
    <Dialog open={isOpen} onClose={closeSuccess}>
      <DialogBackdrop className="fixed inset-0 bg-black/30" />

      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="bg-base-dark/70 fixed inset-0" aria-hidden="true" />
        <DialogPanel className="border-base-lighter relative z-50 w-full max-w-2xl rounded-sm border bg-white shadow-lg">
          <div className="border-base-lighter border-b px-6 py-4">
            <DialogTitle className="font-merriweather text-gray-90 text-xl font-bold">
              {isEditing ? 'Edit custom section' : 'Add a custom section'}
            </DialogTitle>
          </div>
          <div className="px-6 py-5">
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
          </div>
          <div className="border-base-lighter flex justify-end gap-2 border-t px-6 py-4">
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

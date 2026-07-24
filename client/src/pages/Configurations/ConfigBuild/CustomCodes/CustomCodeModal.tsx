import { Button } from '@components/Button';
import {
  getGetConfigurationQueryKey,
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useValidateCustomCodeFromConfiguration,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useToast } from '../../../../hooks/useToast';
import { TextInput } from '@components/TextInput';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Modal, ModalTitle, ModalHeader, ModalBody } from '@components/Modal';
import { Select, SelectContainer } from '@components/Select';
import { useGetCodeSystems } from '../../../../api/code-systems/code-systems';
import { Spinner } from '@components/Spinner';
import { CustomCodeResponse } from '../../../../api/schemas';

interface CustomCodeModalProps {
  configurationId: string;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  selectedCustomCode: CustomCodeResponse | null;
  onClose: () => void;
}

export function CustomCodeModal({
  configurationId,
  isOpen,
  setIsOpen,
  selectedCustomCode,

  onClose,
}: CustomCodeModalProps) {
  const formKey = useMemo(
    () => `${isOpen ? 'open' : 'closed'}-${selectedCustomCode?.code ?? 'new'}`,
    [isOpen, selectedCustomCode?.code]
  );

  const handleCloseCustomCodeModal = () => {
    onClose();
    setIsOpen(false);
  };

  return (
    <Modal open={isOpen} onClose={handleCloseCustomCodeModal}>
      <ModalHeader>
        <ModalTitle>
          {selectedCustomCode ? 'Edit custom code' : 'Add custom code'}
        </ModalTitle>
      </ModalHeader>
      <ModalBody>
        {isOpen && (
          <CustomCodeForm
            key={formKey}
            configurationId={configurationId}
            onClose={handleCloseCustomCodeModal}
            selectedCustomCode={selectedCustomCode}
          />
        )}
      </ModalBody>
    </Modal>
  );
}

type CustomCodeFormProps = Pick<
  CustomCodeModalProps,
  'selectedCustomCode' | 'configurationId' | 'onClose'
>;

function CustomCodeForm({
  selectedCustomCode,
  configurationId,
  onClose,
}: CustomCodeFormProps) {
  const { mutate: addCode } = useAddCustomCodeToConfiguration();
  const { mutate: editCode } = useEditCustomCodeFromConfiguration();
  const { mutate: validateCode } = useValidateCustomCodeFromConfiguration();
  const queryClient = useQueryClient();
  const showToast = useToast();

  const { data: codeSystems, isPending, isError } = useGetCodeSystems();

  const [name, setName] = useState(selectedCustomCode?.display ?? '');
  const [code, setCode] = useState(selectedCustomCode?.code ?? '');

  const [selectedSystemId, setSelectedSystemId] = useState(
    selectedCustomCode?.system_id ?? ''
  );

  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isButtonEnabled = code && selectedSystemId && name && !error;

  const handleCodeUpdate = (code: string) => {
    setCode(code);
  };

  const handleCodeBlur = () => {
    setIsValidating(true);

    const trimmedCode = code.trim();
    handleCodeUpdate(trimmedCode);

    validateCode(
      {
        configurationId,
        data: {
          current_code: selectedCustomCode?.code ?? null,
          desired_code: trimmedCode,
        },
      },
      {
        onSuccess: (resp) => {
          setIsValidating(false);
          if (!resp.data.valid) {
            setError(`The code "${trimmedCode}" already exists.`);
          }
        },
        onError: () => {
          setIsValidating(false);
          showToast({
            variant: 'error',
            heading: 'Validation failed',
            body: 'Could not validate the code. Please try again.',
          });
        },
      }
    );
  };

  const handleSubmit = () => {
    if (selectedCustomCode) {
      editCode(
        {
          configurationId,
          data: {
            id: selectedCustomCode.id,
            code: code.trim() || selectedCustomCode.code,
            system_id: selectedSystemId || selectedCustomCode.system_id,
            display: name.trim() || selectedCustomCode.display,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code updated', body: code });
            onClose();
          },
          onError: () => {
            showToast({
              variant: 'error',
              heading: 'Custom code update failed',
              body: 'The code/system pair already exists.',
            });
            onClose();
          },
        }
      );
    } else {
      addCode(
        {
          configurationId,
          data: {
            code: code.trim(),
            system_id: selectedSystemId,
            display: name.trim(),
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code added', body: code });
            onClose();
          },
        }
      );
    }
  };

  if (isPending)
    return (
      <div className="flex w-full justify-center">
        <Spinner />
      </div>
    );

  if (isError || !codeSystems) return 'Error!';

  return (
    <>
      <Field>
        <Label>Code</Label>
        <TextInput
          type="text"
          value={code}
          onChange={(e) => {
            if (error) setError(null); // clear error on change
            handleCodeUpdate(e.target.value);
          }}
          onBlur={handleCodeBlur}
          autoFocus // eslint-disable-line jsx-a11y/no-autofocus -- focus first input on modal open for keyboard/screen reader users
        />
      </Field>
      {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
      <SelectContainer>
        <Field>
          <Label>Code system</Label>
          <Select
            value={selectedSystemId}
            onChange={(e) => setSelectedSystemId(e.target.value)}
          >
            <option value="" disabled>
              Select system
            </option>
            {codeSystems.data.map((s) => (
              <option key={s.id} value={s.id}>
                {s.display_name}
              </option>
            ))}
          </Select>
        </Field>
      </SelectContainer>
      <Field>
        <Label>Display name</Label>
        <TextInput
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
          }}
        />
      </Field>

      <div className="self-end">
        <Button
          onClick={handleSubmit}
          disabled={!isButtonEnabled || isValidating}
          variant="primary"
        >
          {selectedCustomCode ? 'Update' : 'Add custom code'}
        </Button>
      </div>
    </>
  );
}

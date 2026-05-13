import { Button } from '@components/Button';
import {
  getGetConfigurationQueryKey,
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useValidateCustomCodeFromConfiguration,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { DbConfigurationCustomCode } from '../../../../api/schemas';
import { useToast } from '../../../../hooks/useToast';
import { TextInput } from '@components/TextInput';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Modal, ModalTitle, ModalHeader, ModalBody } from '@components/Modal';
import { Select, SelectContainer } from '@components/Select';
import { useGetCodeSystems } from '../../../../api/code-systems/code-systems';
import { Spinner } from '@components/Spinner';

interface CustomCodeModalProps {
  configurationId: string;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  selectedCustomCode: DbConfigurationCustomCode | null;
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

  const {
    data: supportedCodeSystems,
    isPending,
    isError,
  } = useGetCodeSystems();

  const [name, setName] = useState(selectedCustomCode?.name ?? '');
  const [code, setCode] = useState(selectedCustomCode?.code ?? '');
  const [system, setSystem] = useState(selectedCustomCode?.system ?? '');

  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isButtonEnabled = code && system && name && !error;

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
            code: selectedCustomCode.code,
            system: selectedCustomCode.system,
            name: selectedCustomCode.name,
            new_code: code.trim(),
            new_system: system,
            new_name: name.trim(),
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
            system: system,
            name: name.trim(),
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

  if (isError || !supportedCodeSystems) return 'Error!';

  const systemValues = [
    {
      display_name: 'Select system',
      name: '',
      oid: '',
      id: 'c107a769-4de6-4b3f-bdf0-261284259cfd',
    },
    ...supportedCodeSystems.data,
  ];
  return (
    <>
      <Field>
        <Label>Code #</Label>
        <TextInput
          type="text"
          value={code}
          onChange={(e) => {
            if (error) setError(null); // clear error on change
            handleCodeUpdate(e.target.value);
          }}
          onBlur={handleCodeBlur}
          autoFocus
        />
      </Field>
      {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
      <SelectContainer>
        <Field>
          <Label>Code system</Label>
          <Select value={system} onChange={(e) => setSystem(e.target.value)}>
            {systemValues.map((s) => (
              <option key={s.id} value={s.name}>
                {s.display_name}
              </option>
            ))}
          </Select>
        </Field>
      </SelectContainer>
      <Field>
        <Label>Code name</Label>
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

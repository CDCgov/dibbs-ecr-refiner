import { Select, Label as USWDSLabel } from '@trussworks/react-uswds';
import { Button } from '@components/Button';
import {
  getGetConfigurationQueryKey,
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
  useValidateCustomCodeFromConfiguration,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { DbConfigurationCustomCode, CodeSystem } from '../../../../api/schemas';
import { useToast } from '../../../../hooks/useToast';
import { TextInput } from '@components/TextInput';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Modal, ModalTitle, ModalHeader, ModalBody } from '@components/Modal';

interface CustomCodeModalProps {
  configurationId: string;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  selectedCustomCode: DbConfigurationCustomCode | null;
  onClose: () => void;
}

function normalizeSystem(system: CodeSystem | string): CodeSystem {
  return system.toLowerCase() as CodeSystem;
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

  // TODO: this should come from the server.
  // Maybe get this info as part of the seed script?
  const systemValues = [
    { name: 'Select system', value: '' },
    ...Object.values(CodeSystem).map((s) => ({
      name: s,
      value: s.toLowerCase(),
    })),
  ];

  const [name, setName] = useState(selectedCustomCode?.name ?? '');
  const [code, setCode] = useState(selectedCustomCode?.code ?? '');
  const [system, setSystem] = useState(selectedCustomCode?.system ?? '');
  const [error, setError] = useState<string | null>(null);

  const isButtonEnabled = code && system && name;

  const handleCodeUpdate = (code: string) => {
    const trimmedCode = code.trim();
    setCode(trimmedCode);
  };

  const handleCodeBlur = () => {
    const trimmedCode = code.trim();
    handleCodeUpdate(trimmedCode);

    // Skip server validation if code hasn't changed (no-op edit)
    if (selectedCustomCode && trimmedCode === selectedCustomCode.code) return;

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
          if (!resp.data.valid) {
            setError(`The code "${trimmedCode}" is already in use.`);
          }
        },
        onError: () => {
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
            system: normalizeSystem(selectedCustomCode.system),
            name: selectedCustomCode.name,
            new_code: code.trim(),
            new_system: normalizeSystem(system),
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
            system: normalizeSystem(system),
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

  return (
    <>
      <Field>
        <Label>Code #</Label>
        <TextInput
          type="text"
          value={code}
          onChange={(e) => {
            if (error) setError(''); // clear error on change
            handleCodeUpdate(e.target.value);
          }}
          onBlur={handleCodeBlur}
          autoFocus
        />
      </Field>
      {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
      <div>
        <USWDSLabel htmlFor="system">Code system</USWDSLabel>
        <Select
          id="system"
          name="system"
          value={normalizeSystem(system)}
          onChange={(e) => setSystem(normalizeSystem(e.target.value))}
        >
          {systemValues.map((sv) => (
            <option key={sv.value} value={sv.value}>
              {sv.name}
            </option>
          ))}
        </Select>
      </div>

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
          disabled={!isButtonEnabled || !!error} // disable if form invalid or error exists
          variant="primary"
        >
          {selectedCustomCode ? 'Update' : 'Add custom code'}
        </Button>
      </div>
    </>
  );
}

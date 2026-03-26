import {
  Icon,
  Label,
  Modal,
  ModalFooter,
  ModalHeading,
  ModalRef,
  Select,
  TextInput,
} from '@trussworks/react-uswds';
import { Button } from '../../../../components/Button';
import {
  getGetConfigurationQueryKey,
  useAddCustomCodeToConfiguration,
  useEditCustomCodeFromConfiguration,
} from '../../../../api/configurations/configurations';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { DbConfigurationCustomCode, CodeSystem } from '../../../../api/schemas';
import { useToast } from '../../../../hooks/useToast';

interface CustomCodeModalProps {
  configurationId: string;
  modalRef: React.RefObject<ModalRef | null>;
  onClose: () => void;
  selectedCustomCode: DbConfigurationCustomCode | null;
  deduplicated_codes: string[];
}

function normalizeSystem(system: CodeSystem | string): CodeSystem {
  return system.toLowerCase() as CodeSystem;
}

export function CustomCodeModal({
  configurationId,
  modalRef,
  onClose,
  selectedCustomCode,
  deduplicated_codes,
}: CustomCodeModalProps) {
  const { mutate: addCode } = useAddCustomCodeToConfiguration();
  const { mutate: editCode } = useEditCustomCodeFromConfiguration();
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

  const [form, setForm] = useState({
    code: selectedCustomCode?.code ?? '',
    system: selectedCustomCode?.system
      ? normalizeSystem(selectedCustomCode.system)
      : '',
    name: selectedCustomCode?.name ?? '',
  });

  if (
    form.code === '' &&
    form.name === '' &&
    form.system === '' &&
    selectedCustomCode
  ) {
    setForm({
      code: selectedCustomCode?.code ?? '',
      system: selectedCustomCode?.system
        ? normalizeSystem(selectedCustomCode.system)
        : '',
      name: selectedCustomCode?.name ?? '',
    });
  }

  const [error, setError] = useState<string | null>(null);

  function resetForm() {
    setForm({ code: '', system: '', name: '' });
  }

  const isButtonEnabled =
    form.code && form.system && form.system !== '' && form.name;

  const handleChange =
    (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (selectedCustomCode) {
      editCode(
        {
          configurationId,
          data: {
            code: selectedCustomCode.code,
            system: normalizeSystem(selectedCustomCode.system),
            name: selectedCustomCode.name,
            new_code: form.code,
            new_system: normalizeSystem(form.system),
            new_name: form.name,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code updated', body: form.code });
            resetForm();
            onClose();
          },
          onError: () => {
            showToast({
              variant: 'error',
              heading: 'Custom code update failed',
              body: 'The code/system pair already exists.',
            });
            resetForm();
            onClose();
          },
        }
      );
    } else {
      addCode(
        {
          configurationId,
          data: {
            code: form.code,
            system: normalizeSystem(form.system),
            name: form.name,
          },
        },
        {
          onSuccess: async () => {
            await queryClient.invalidateQueries({
              queryKey: getGetConfigurationQueryKey(configurationId),
            });
            showToast({ heading: 'Custom code added', body: form.code });
            resetForm();
            onClose();
          },
        }
      );
    }
  };

  return (
    <Modal
      ref={modalRef}
      id="custom-code-modal"
      aria-describedby="modal-heading"
      aria-labelledby="modal-heading"
      isLarge
      className="max-w-100!"
      forceAction
    >
      <ModalHeading
        id="modal-heading"
        className="text-bold font-merriweather mb-6 p-0! text-xl"
      >
        {selectedCustomCode ? 'Edit custom code' : 'Add custom code'}
      </ModalHeading>

      <Button
        aria-label="Close this window"
        onClick={() => {
          resetForm();
          onClose();
        }}
        className="absolute top-4 right-0 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
      >
        <Icon.Close className="h-6! w-6!" aria-hidden />
      </Button>

      <div className="mt-5 flex flex-col gap-5 p-0!">
        <div>
          <Label htmlFor="code">Code #</Label>
          <TextInput
            id="code"
            name="code"
            type="text"
            value={form.code}
            onChange={(e) => {
              const value = e.target.value.trimStart(); // trim leading space only while typing
              setForm((prev) => ({ ...prev, code: value }));
              if (error) setError(''); // clear error on change
            }}
            onBlur={() => {
              const trimmedCode = form.code.trim(); // full trim (leading + trailing)
              if (deduplicated_codes.includes(trimmedCode)) {
                setError(`The code "${trimmedCode}" already exists.`);
              } else {
                setForm((prev) => ({ ...prev, code: trimmedCode })); // ensure stored value is clean
              }
            }}
            autoComplete="off"
          />
          {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
        </div>
        <div>
          <Label htmlFor="system">Code system</Label>
          <Select
            id="system"
            name="system"
            value={form.system}
            onChange={handleChange('system')}
          >
            {systemValues.map((sv) => (
              <option key={sv.value} value={sv.value}>
                {sv.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="name">Code name</Label>
          <TextInput
            id="name"
            name="name"
            type="text"
            value={form.name}
            onChange={handleChange('name')}
            autoComplete="off"
          />
        </div>
      </div>

      <ModalFooter className="flex justify-end p-0">
        <Button
          onClick={(e) =>
            handleSubmit(e as unknown as React.FormEvent<HTMLFormElement>)
          }
          disabled={!isButtonEnabled || !!error} // disable if form invalid or error exists
          variant="primary"
          className="m-0!"
        >
          {selectedCustomCode ? 'Update' : 'Add custom code'}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

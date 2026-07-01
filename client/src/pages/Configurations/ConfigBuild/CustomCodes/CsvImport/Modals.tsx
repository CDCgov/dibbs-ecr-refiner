import {
  IndexedCodeSystem,
  UploadCustomCodesInput,
  UploadCustomCodesPreviewItem,
} from '../../../../../api/schemas';

import { Button } from '@components/Button';
import { TextInput } from '@components/TextInput';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Select, SelectContainer } from '@components/Select';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { useState, ChangeEvent } from 'react';
import { UploadError } from './ImportCustomCodes';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  handleConfirm: () => void;
}

export function ConfirmModal({
  isOpen,
  onClose,
  handleConfirm,
}: ConfirmModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Confirm & save codes?</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p>
          Once you save the codes, you will need to edit or delete them
          individually.
        </p>
      </ModalBody>
      <ModalFooter align="right">
        <Button variant="primary" onClick={handleConfirm}>
          Yes, save codes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

interface UndoModalProps {
  isOpen: boolean;
  onClose: () => void;
  handleDelete: () => void;
}

export function UndoModal({ isOpen, onClose, handleDelete }: UndoModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Undo & delete codes</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p>
          Are you sure you want to delete all these uploaded codes? If you want
          to add this list of codes again, you will need to re-upload the
          spreadsheet.
        </p>
      </ModalBody>
      <ModalFooter align="right">
        <Button
          variant="primary"
          onClick={() => {
            onClose();
            handleDelete();
          }}
        >
          Undo & delete codes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

interface PreviewEditModalProps {
  previewEditItem: UploadCustomCodesPreviewItem;
  previewItems: UploadCustomCodesPreviewItem[] | null;
  setPreviewItems: React.Dispatch<
    React.SetStateAction<UploadCustomCodesPreviewItem[]>
  >;
  closePreviewEditModal: () => void;
  setError: React.Dispatch<React.SetStateAction<UploadError | null>>;
  error: UploadError | null;
  codeSystems: IndexedCodeSystem;
}

export function PreviewEditModal({
  previewEditItem,
  previewItems,
  setPreviewItems,
  closePreviewEditModal,
  setError,
  error,
  codeSystems,
}: PreviewEditModalProps) {
  const [previewEditForm, setPreviewEditForm] = useState(previewEditItem);

  const handlePreviewEditSubmit = (
    payload: UploadCustomCodesPreviewItem | null
  ) => {
    if (!payload) {
      closePreviewEditModal();
      return;
    }
    setPreviewItems((prev) =>
      prev
        ? prev.map((item) => (payload.id === item.id ? { ...payload } : item))
        : prev
    );
    closePreviewEditModal();
  };

  function handlePreviewEditChange<K extends keyof UploadCustomCodesInput>(
    field: K,
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    const value = event.target.value as UploadCustomCodesInput[K];
    setPreviewEditForm((prev) => {
      return {
        ...prev,
        [field]: value,
      };
    });
  }

  const isEditSaveDisabled =
    error != null ||
    !previewEditForm ||
    !previewEditForm.code ||
    !previewEditForm.name ||
    !previewEditForm.system_key;

  return (
    <Modal open={true} onClose={closePreviewEditModal}>
      <ModalHeader>
        <ModalTitle>
          {previewEditItem?.code ? `Edit ${previewEditItem.code}` : 'Edit code'}
        </ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div>
          <Field>
            <Label>Code</Label>
            <TextInput
              type="text"
              value={previewEditForm?.code}
              onChange={(e) => handlePreviewEditChange('code', e)}
              onBlur={() => {
                const trimmedCode = previewEditForm?.code.trim();
                if (
                  previewItems?.some(
                    (item) =>
                      item.code === trimmedCode &&
                      item.id !== previewEditForm?.id
                  )
                ) {
                  setError({
                    message: `The code "${trimmedCode}" already exists.`,
                  });
                } else {
                  setPreviewEditForm((prev) => ({
                    ...prev,
                    code: trimmedCode,
                  }));
                  setError(null);
                }
              }}
              autoFocus // eslint-disable-line jsx-a11y/no-autofocus -- focus first input on modal open for keyboard/screen reader users
            />
          </Field>
          {error && (
            <p className="mb-1 text-sm text-red-600">{error.message}</p>
          )}
        </div>
        <SelectContainer>
          <Field>
            <Label>Code system</Label>
            <Select
              value={previewEditForm.system_key}
              onChange={(e) => handlePreviewEditChange('system_key', e)}
            >
              {Object.values(codeSystems).map((s) => (
                <option key={s.id} value={s.key}>
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
            value={previewEditForm.name}
            onChange={(e) => handlePreviewEditChange('name', e)}
          />
        </Field>
      </ModalBody>
      <ModalFooter align="right">
        <Button
          onClick={() => handlePreviewEditSubmit(previewEditForm)}
          disabled={isEditSaveDisabled}
          variant="primary"
        >
          Save changes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

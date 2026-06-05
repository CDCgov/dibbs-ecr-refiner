import React from 'react';
import { UploadCustomCodesPreviewItem } from '../../../../../api/schemas';

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
import { useGetCodeSystems } from '../../../../../api/code-systems/code-systems';
import { Spinner } from '@components/Spinner';

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
  isOpen: boolean;
  closePreviewEditModal: () => void;
  previewEditForm: UploadCustomCodesPreviewItem;
  setPreviewEditForm: React.Dispatch<
    React.SetStateAction<UploadCustomCodesPreviewItem>
  >;
  isEditSaveDisabled: boolean;
  handlePreviewEditSubmit: () => void;
  previewItems: UploadCustomCodesPreviewItem[] | null;
  previewEditIndex: number | null;
  setError: (err: string | null) => void;
  error: string | null;
  handlePreviewEditChange: (
    field: keyof UploadCustomCodesPreviewItem
  ) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

export function PreviewEditModal({
  isOpen,
  closePreviewEditModal,
  previewEditForm,
  setPreviewEditForm,
  isEditSaveDisabled,
  handlePreviewEditSubmit,
  previewItems,
  previewEditIndex,
  setError,
  error,
  handlePreviewEditChange,
}: PreviewEditModalProps) {
  const { data: codeSystems, isPending, isError } = useGetCodeSystems();

  if (isPending)
    return (
      <div className="flex w-full justify-center">
        <Spinner />
      </div>
    );

  if (isError || !codeSystems) return 'Error!';

  return (
    <Modal open={isOpen} onClose={closePreviewEditModal}>
      <ModalHeader>
        <ModalTitle>
          {previewEditForm.code ? `Edit ${previewEditForm.code}` : 'Edit code'}
        </ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div>
          <Field>
            <Label>Code #</Label>
            <TextInput
              type="text"
              value={previewEditForm.code}
              onChange={handlePreviewEditChange('code')}
              onBlur={() => {
                const trimmedCode = previewEditForm.code.trim();
                if (
                  previewItems?.some(
                    (item, idx) =>
                      item.code === trimmedCode && idx !== previewEditIndex
                  )
                ) {
                  setError(`The code "${trimmedCode}" already exists.`);
                } else {
                  setPreviewEditForm((prev) => ({
                    ...prev,
                    code: trimmedCode,
                  }));
                  setError(null);
                }
              }}
              autoFocus
            />
          </Field>
          {error && <p className="mb-1 text-sm text-red-600">{error}</p>}
        </div>
        <SelectContainer>
          <Field>
            <Label>Code system</Label>
            <Select
              value={previewEditForm.system_key}
              onChange={handlePreviewEditChange('system_key')}
            >
              {codeSystems.data.map((s) => (
                <option key={s.id} value={s.key}>
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
            value={previewEditForm.name}
            onChange={handlePreviewEditChange('name')}
          />
        </Field>
      </ModalBody>
      <ModalFooter align="right">
        <Button
          onClick={handlePreviewEditSubmit}
          disabled={isEditSaveDisabled}
          variant="primary"
        >
          Save changes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

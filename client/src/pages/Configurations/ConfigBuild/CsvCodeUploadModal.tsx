import React from 'react';
import { Label as USWDSLabel, Select } from '@trussworks/react-uswds';
import { CodeSystem, UploadCustomCodesPreviewItem } from '../../../api/schemas';

import { Button } from '../../../components/Button';
import { TextInput } from '../../../components/TextInput';
import { Field } from '../../../components/Field';
import { Label } from '../../../components/Label';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '../../../components/Modal';

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
  PREVIEW_CODE_SYSTEMS: CodeSystem[];
  previewItems: UploadCustomCodesPreviewItem[] | null;
  previewEditIndex: number | null;
  setError: (err: string | null) => void;
  error: string | null;
  handlePreviewEditChange: (
    field: 'code' | 'system' | 'name'
  ) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

export function PreviewEditModal({
  isOpen,
  closePreviewEditModal,
  previewEditForm,
  setPreviewEditForm,
  isEditSaveDisabled,
  handlePreviewEditSubmit,
  PREVIEW_CODE_SYSTEMS,
  previewItems,
  previewEditIndex,
  setError,
  error,
  handlePreviewEditChange,
}: PreviewEditModalProps) {
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
        <div>
          <USWDSLabel htmlFor="preview-edit-system">Code system</USWDSLabel>
          <Select
            id="preview-edit-system"
            name="preview-edit-system"
            value={previewEditForm.system}
            onChange={handlePreviewEditChange('system')}
          >
            {PREVIEW_CODE_SYSTEMS.map((system: string) => (
              <option key={system} value={system}>
                {system}
              </option>
            ))}
          </Select>
        </div>
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

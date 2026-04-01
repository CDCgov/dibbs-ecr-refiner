import React from 'react';
import {
  Modal,
  ModalRef,
  ModalHeading,
  ModalFooter,
  Icon,
  Label as USWDSLabel,
  Select,
} from '@trussworks/react-uswds';
import { CodeSystem, UploadCustomCodesPreviewItem } from '../../../api/schemas';

import { Button } from '../../../components/Button';
import { TextInput } from '../../../components/TextInput';
import { Field } from '../../../components/Field';
import { Label } from '../../../components/Label';

// Confirm Modal
interface ConfirmModalProps {
  confirmModalRef: React.RefObject<ModalRef | null>;
  closeConfirmModal: () => void;
  handleConfirm: () => void;
}

export function ConfirmModal({
  confirmModalRef,
  closeConfirmModal,
  handleConfirm,
}: ConfirmModalProps) {
  return (
    <Modal
      ref={confirmModalRef}
      id="csv-confirm-modal"
      aria-describedby="csv-confirm-description"
      aria-labelledby="csv-confirm-heading"
      forceAction
    >
      <Button
        aria-label="Close this window"
        onClick={closeConfirmModal}
        variant="tertiary"
        className="absolute top-4 right-2 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
      >
        <Icon.Close className="h-5 w-5" aria-hidden />
      </Button>
      <ModalHeading id="csv-confirm-heading">
        Confirm & save codes?
      </ModalHeading>
      <div id="csv-confirm-description" className="mt-4 text-sm text-gray-700">
        Once you save the codes, you will need to edit or delete them
        individually.
      </div>
      <ModalFooter className="flex justify-end gap-2">
        <Button variant="primary" onClick={handleConfirm}>
          Yes, save codes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

// Undo Modal
interface UndoModalProps {
  undoModalRef: React.RefObject<ModalRef | null>;
  closeUndoModal: () => void;
  handleDelete: () => void;
}

export function UndoModal({
  undoModalRef,
  closeUndoModal,
  handleDelete,
}: UndoModalProps) {
  return (
    <Modal
      ref={undoModalRef}
      id="csv-undo-modal"
      aria-describedby="csv-undo-description"
      aria-labelledby="csv-undo-heading"
      forceAction
    >
      <Button
        aria-label="Close this window"
        onClick={closeUndoModal}
        variant="tertiary"
        className="absolute top-4 right-2 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
      >
        <Icon.Close className="h-5 w-5" aria-hidden />
      </Button>
      <ModalHeading id="csv-undo-heading">Undo & delete codes</ModalHeading>
      <div id="csv-undo-description" className="mt-4 text-sm text-gray-700">
        Are you sure you want to delete all these uploaded codes? If you want to
        add this list of codes again, you will need to re-upload the
        spreadsheet.
      </div>
      <ModalFooter className="flex justify-end gap-2">
        <Button
          variant="primary"
          onClick={() => {
            closeUndoModal();
            handleDelete();
          }}
        >
          Undo & delete codes
        </Button>
      </ModalFooter>
    </Modal>
  );
}

// PreviewEdit Modal
interface PreviewEditModalProps {
  previewEditModalRef: React.RefObject<ModalRef | null>;
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
  previewEditModalRef,
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
    <Modal
      ref={previewEditModalRef}
      id="preview-edit-modal"
      aria-describedby="preview-edit-description"
      aria-labelledby="preview-edit-heading"
      isLarge
      className="max-w-100!"
      forceAction
    >
      <Button
        aria-label="Close this window"
        onClick={closePreviewEditModal}
        variant="tertiary"
        className="absolute top-4 right-2 h-3 w-3 rounded bg-transparent! p-0! text-gray-500! hover:cursor-pointer hover:bg-gray-100 hover:text-gray-900"
      >
        <Icon.Close className="h-5 w-5" aria-hidden />
      </Button>
      <ModalHeading
        id="preview-edit-heading"
        className="text-bold font-merriweather mb-6 p-0! text-xl"
      >
        {previewEditForm.code ? `Edit ${previewEditForm.code}` : 'Edit code'}
      </ModalHeading>
      <div
        id="preview-edit-description"
        className="mt-5 flex flex-col gap-5 p-0!"
      >
        <div>
          <Field>
            <Label>Code #</Label>
            <TextInput
              id="preview-edit-code"
              name="preview-edit-code"
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
              autoComplete="off"
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
      </div>
      <ModalFooter className="flex justify-end gap-2">
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

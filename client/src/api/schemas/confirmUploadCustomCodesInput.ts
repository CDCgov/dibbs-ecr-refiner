import type { UploadCustomCodesPreviewItem } from './uploadCustomCodesPreviewItem';

/**
 * Payload used to confirm a previously validated CSV import.
 */
export interface ConfirmUploadCustomCodesInput {
  custom_codes: UploadCustomCodesPreviewItem[];
}

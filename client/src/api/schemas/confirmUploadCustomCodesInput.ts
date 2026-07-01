import type { UploadCustomCodesInput } from './uploadCustomCodesInput';

/**
 * Payload used to confirm a previously validated CSV import.
 */
export interface ConfirmUploadCustomCodesInput {
  custom_codes: UploadCustomCodesInput[];
}

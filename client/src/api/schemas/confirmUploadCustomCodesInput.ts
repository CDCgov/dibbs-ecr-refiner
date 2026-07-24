import type { AddCustomCodeInput } from './addCustomCodeInput';

/**
 * Payload used to confirm a previously validated CSV import.
 */
export interface ConfirmUploadCustomCodesInput {
  custom_codes: AddCustomCodeInput[];
}

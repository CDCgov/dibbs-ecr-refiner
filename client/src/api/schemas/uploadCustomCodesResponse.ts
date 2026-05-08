import type { UploadCustomCodesResponseErrors } from './uploadCustomCodesResponseErrors';

/**
 * CSV response model. Errors are surfaced via the `errors` array.
 */
export interface UploadCustomCodesResponse {
  message?: string | null;
  codes_processed?: number | null;
  total_custom_codes_in_configuration?: number | null;
  errors?: UploadCustomCodesResponseErrors;
}

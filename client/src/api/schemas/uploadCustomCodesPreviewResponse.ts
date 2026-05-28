import type { UploadCustomCodesPreviewItem } from './uploadCustomCodesPreviewItem';
import type { UploadCustomCodesPreviewResponseCodeSystems } from './uploadCustomCodesPreviewResponseCodeSystems';

/**
 * Validated CSV preview for delayed confirmation; only valid if preview.
 */
export interface UploadCustomCodesPreviewResponse {
  preview: UploadCustomCodesPreviewItem[];
  code_systems: UploadCustomCodesPreviewResponseCodeSystems;
  codes_processed?: number | null;
  total_custom_codes_in_configuration?: number | null;
}

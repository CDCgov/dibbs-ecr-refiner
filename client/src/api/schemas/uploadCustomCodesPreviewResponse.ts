import type { CodeSystemIndex } from './codeSystemIndex';
import type { UploadCustomCodesPreviewItem } from './uploadCustomCodesPreviewItem';

/**
 * Validated CSV preview for delayed confirmation; only valid if preview.
 */
export interface UploadCustomCodesPreviewResponse {
  preview: UploadCustomCodesPreviewItem[];
  code_systems: CodeSystemIndex;
  codes_processed?: number | null;
  total_custom_codes_in_configuration?: number | null;
}

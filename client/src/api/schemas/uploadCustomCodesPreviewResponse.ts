import type { IndexedCodeSystem } from './indexedCodeSystem';
import type { UploadCustomCodesPreviewItem } from './uploadCustomCodesPreviewItem';

/**
 * Validated CSV preview for delayed confirmation; only valid if preview.
 */
export interface UploadCustomCodesPreviewResponse {
  preview_items: UploadCustomCodesPreviewItem[];
  code_systems: IndexedCodeSystem;
  codes_processed?: number | null;
  total_custom_codes_in_configuration?: number | null;
}

import type { DbCodeSystem } from './dbCodeSystem';
import type { UploadCustomCodesPreviewItem } from './uploadCustomCodesPreviewItem';

/**
 * Validated CSV preview for delayed confirmation; only valid if preview.
 */
export interface UploadCustomCodesPreviewResponse {
  preview_items: UploadCustomCodesPreviewItem[];
  codes_processed?: number | null;
  total_custom_codes_in_configuration?: number | null;
  code_systems: DbCodeSystem[];
}


/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  id: string;
  code: string;
  system_id: string;
  system_display_name: string;
  display_name: string;
  row?: number | null;
}

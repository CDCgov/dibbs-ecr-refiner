
/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  id: string;
  code: string;
  system_id: string;
  system_name: string;
  display: string;
  row?: number | null;
}

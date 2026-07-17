
/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  code: string;
  system_id: string;
  display: string;
  id: string;
  system_name: string;
  row?: number | null;
}

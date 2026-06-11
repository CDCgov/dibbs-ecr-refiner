
/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  id: string;
  code: string;
  system_key: string;
  name: string;
  row?: number | null;
}

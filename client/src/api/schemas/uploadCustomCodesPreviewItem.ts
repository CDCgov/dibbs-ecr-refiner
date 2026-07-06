
/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  code: string;
  system_key: string;
  name: string;
  id: string;
  row?: number | null;
}

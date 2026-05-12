
/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  code: string;
  system: string;
  name: string;
  row?: number | null;
}

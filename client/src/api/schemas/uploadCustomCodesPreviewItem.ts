import type { CodeSystem } from './codeSystem';

/**
 * Validated CSV row ready for confirmation.
 */
export interface UploadCustomCodesPreviewItem {
  code: string;
  system: CodeSystem;
  name: string;
  row?: number | null;
}

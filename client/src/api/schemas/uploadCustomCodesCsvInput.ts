
/**
 * Input model for Custom Code CSV.
 */
export interface UploadCustomCodesCsvInput {
  /** Full CSV contents as UTF-8 text */
  csv_text: string;
  filename?: string | null;
}

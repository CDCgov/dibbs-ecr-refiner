
/**
 * Utility class to help Orval ship these values to the frontend.
 */
export const FileInfoResponseValue = {
  max_for_diff_rendering_mb: 2,
  max_for_uncompressed_mb: 15,
} as const;
export type FileInfoResponse = typeof FileInfoResponseValue;

import type { SerializedFile } from './serializedFile';

/**
 * The three files an active configuration serializes to.
 */
export interface SerializedFilesResponse {
  active: SerializedFile;
  current: SerializedFile;
  metadata: SerializedFile;
}

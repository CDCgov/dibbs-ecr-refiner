import type { SerializedFile } from './serializedFile';

/**
 * Dataclass for serialized file data.
 */
export interface SerializedFiles {
  active: SerializedFile;
  current: SerializedFile;
  metadata: SerializedFile;
}


/**
 * One serialized configuration file, as stored in S3.
 */
export interface SerializedFile {
  key: string;
  content: string;
}

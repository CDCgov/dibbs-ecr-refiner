import type { IndependentTestInput } from './independentTestInput';

export interface BodyUploadEcr {
  body: IndependentTestInput;
  uploaded_file?: Blob | null;
}

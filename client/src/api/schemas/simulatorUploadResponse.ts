import type { Condition } from './condition';
import type { FileInfoResponse } from './fileInfoResponse';

/**
 * Model for the response when uploading a document in the simulate testing suite.
 */
export interface SimulatorUploadResponse {
  message: string;
  conditions_without_matching_configs: string[];
  conditions_without_active_configs: string[];
  refined_conditions_found: number;
  refined_conditions: Condition[];
  unrefined_eicr: string;
  refined_download_key: string;
  file_info_response: FileInfoResponse;
}

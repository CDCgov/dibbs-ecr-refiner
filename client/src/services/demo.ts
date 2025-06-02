export class ApiUploadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiUploadError';
    Object.setPrototypeOf(this, ApiUploadError.prototype);
  }
}

export interface RefinedOutput {
  refined_eicr: string;
  reportable_condition: Condition;
  refined_download_token: string;
  output_file_name: string;
  stats: string[];
}

export interface DemoUploadResponse {
  unrefined_eicr: string;
  reportable_conditions: Condition[];
  refined_outputs: RefinedOutput[];
}

type Condition = {
  code: string;
  displayName: string;
};

export async function uploadDemoFile(): Promise<DemoUploadResponse> {
  const resp = await fetch('/api/v1/demo/upload');
  if (!resp.ok) {
    throw new ApiUploadError('Unable to perform demo upload.');
  }
  return resp.json();
}

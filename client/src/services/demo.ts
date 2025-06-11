export class ApiUploadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiUploadError';
    Object.setPrototypeOf(this, ApiUploadError.prototype);
  }
}

export interface DemoUploadResponse {
  conditions: Condition[];
  unrefined_eicr: string;
  refined_download_token: string;
}

export interface Condition {
  display_name: string;
  code: string;
  refined_eicr: string;
  stats: string[];
}

export async function uploadDemoFile(
  formData?: FormData
): Promise<DemoUploadResponse> {
  const options: RequestInit = {
    method: 'POST',
    ...(formData ? { body: formData } : {}),
  };

  const resp = await fetch('/api/v1/demo/upload', options);

  if (!resp.ok) {
    throw new ApiUploadError('Unable to perform demo upload.');
  }

  return resp.json();
}

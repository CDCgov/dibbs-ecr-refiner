export class ApiUploadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiUploadError';
    Object.setPrototypeOf(this, ApiUploadError.prototype);
  }
}

export interface DemoUploadResponse {
  unrefined_eicr: string;
  refined_eicr: string;
  stats: string[];
}

export async function uploadDemoFile(): Promise<DemoUploadResponse> {
  const resp = await fetch('/api/v1/demo/upload');
  if (!resp.ok) {
    throw new ApiUploadError('Unable to perform demo upload.');
  }
  return resp.json();
}

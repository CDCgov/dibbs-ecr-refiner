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

interface DemoUploadError {
  detail: string;
}

const uploadRoute = '/api/v1/demo/upload';
/**
 * Allows the client to provide their own `formData`, which will have
 * their .zip file data attached. The server will see this and process the
 * attached information instead of using the sample data.
 * @param formData object containing the client's .zip file data
 * @returns client's processed zip file as JSON data
 */
export async function uploadCustomZipFile(
  selectedFile: File | null
): Promise<DemoUploadResponse> {
  if (!selectedFile) throw Error('File must be provided.');
  const formData = new FormData();

  // The `name` needs to match the UploadFile arg name in the /demo route
  formData.append('uploaded_file', selectedFile);

  const options: RequestInit = {
    method: 'POST',
    body: formData,
  };

  const resp = await fetch(uploadRoute, options);

  if (!resp.ok) {
    const errorResp: DemoUploadError = await resp.json();
    throw new ApiUploadError(errorResp.detail);
  }

  return resp.json();
}

/**
 * Makes a request to the `/upload` route without a body. The server will "upload"
 * a sample eCR that the client can make use of to work through the demo.
 * @returns Sample file JSON data
 */
export async function uploadDemoFile(): Promise<DemoUploadResponse> {
  const options: RequestInit = {
    method: 'POST',
  };

  const resp = await fetch(uploadRoute, options);

  if (!resp.ok) {
    throw new ApiUploadError('Unable to perform demo upload.');
  }

  return resp.json();
}

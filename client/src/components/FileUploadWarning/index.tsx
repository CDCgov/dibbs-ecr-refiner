import { Button } from '../Button';

interface FileUploadWarningProps {
  errorMessage: string;
  reset: () => void;
}

export function FileUploadWarning({
  errorMessage,
  reset,
}: FileUploadWarningProps) {
  return (
    <div className="bg-state-error-lighter flex h-80! w-140! flex-col items-center rounded px-20 py-8">
      <div className="text-state-error-dark pb-2.5">
        <ErrorIcon />
      </div>
      <h2 className="mb-2">Error</h2>
      <p className="mb-2">There was an error uploading the file</p>
      <p className="mb-10 text-center">{errorMessage}</p>

      <Button onClick={reset}>Try again</Button>
    </div>
  );
}

function ErrorIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="54"
      height="54"
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
    </svg>
  );
}

import { Icon } from '@trussworks/react-uswds';
import { Button } from '../Button';

interface FileUploadWarningProps {
  errorMessage: string;
  reset: () => void;
}
export default function FileUploadWarning({
  errorMessage,
  reset,
}: FileUploadWarningProps) {
  return (
    <div className="bg-state-error-lighter flex !h-[20rem] !w-[35rem] flex-col items-center rounded px-20 py-8">
      <Icon.Error
        size={8}
        aria-label="Exclamation point indicating error"
        className="text-state-error-dark pb-2.5"
      />
      <h2 className="mb-2">Error</h2>
      <p className="mb-2">There was an error uploading the file</p>
      <p className="mb-10 text-center">{errorMessage}</p>

      <Button onClick={reset}>Try again</Button>
    </div>
  );
}

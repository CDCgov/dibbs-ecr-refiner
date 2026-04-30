import { Icon } from '@trussworks/react-uswds';

type WarningProps = {
  heading: string;
  message: string;
};

export function Warning({ heading, message }: WarningProps) {
  return (
    <div className="text-state-error-dark bg-state-error-lighter flex w-100 items-start p-4">
      <Icon.Warning aria-hidden className="-mt-0.5 h-5! w-7!" />
      <div className="ml-4">
        <div className="mb-2 font-bold"> {heading}</div>
        <p>{message}</p>
      </div>
    </div>
  );
}

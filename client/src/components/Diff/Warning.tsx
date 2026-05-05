import { Icon } from '@trussworks/react-uswds';

type WarningProps = {
  heading: string;
  message: string;
};

export function Warning({ heading, message }: WarningProps) {
  return (
    <div className="text-state-error-dark bg-state-error-lighter flex w-100 items-start p-4">
      <div className="flex gap-4">
        <Icon.Warning className="h-5! w-7!" aria-hidden />
        <div className="flex flex-col gap-2">
          <p className="font-bold">{heading}</p>
          <p>{message}</p>
        </div>
      </div>
    </div>
  );
}

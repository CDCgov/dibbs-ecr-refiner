import { Icon } from '@trussworks/react-uswds';

type Warning = {
  heading: string;
  message: string;
};

export function Warning({ heading, message }: Warning) {
  return (
    <div className="text-state-error-dark bg-state-error-lighter flex w-100 items-start p-4">
      <Icon.Warning
        aria-label="Warning icon to visually indicate issue with the page"
        className="-mt-0.5 h-5! w-7!"
      ></Icon.Warning>
      <div className="ml-4">
        <div className="mb-2 font-bold"> {heading}</div>
        <p>{message}</p>
      </div>
    </div>
  );
}

import { Alert, AlertProps, HeadingLevel } from '@trussworks/react-uswds';
import classNames from 'classnames';

type ToastProps = {
  variant: AlertProps['type'];
  heading?: string;
  body: string | React.ReactNode;
  headingLevel?: HeadingLevel;
  hideProgressBar?: boolean;
};

/**
 * Don't use `Toast` directly. Instead use the `useToast` hook.
 * @example
 * const showToast = useToast()
 * <Button onClick={() => showToast({header: 'Example header', body: 'Example body'})}
 * >Click me
 * </Button>
 */
export function Toast({
  variant,
  heading,
  body,
  headingLevel = 'h4',
}: ToastProps) {
  return (
    <div className="flex flex-col">
      <div
        className={classNames('mt-4 flex w-full flex-col gap-2 px-5', {
          'bg-state-success-lighter': variant === 'success',
        })}
      >
        <div className="flex gap-1">
          <CircleCheckIcon />
          {heading ? (
            <h4 className="ml-2 text-2xl font-bold whitespace-nowrap text-black">
              {heading}
            </h4>
          ) : null}
        </div>
        <p className="ml-11 text-black">{body}</p>
      </div>
      <Alert
        className="w-full"
        type={variant}
        heading={
          heading ? (
            <span className="usa-alert__heading text-lg font-bold">
              {heading}
            </span>
          ) : null
        }
        headingLevel={heading ? headingLevel : 'h4'}
      >
        {body}
      </Alert>
    </div>
  );
}

function CircleCheckIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      className="shrink-0"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
    </svg>
  );
}

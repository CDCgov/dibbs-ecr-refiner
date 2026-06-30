import classNames from 'classnames';

interface ToastProps {
  variant: 'success' | 'error';
  heading?: string;
  body: string | React.ReactNode;
  hideProgressBar?: boolean;
}

/**
 * Don't use `Toast` directly. Instead use the `useToast` hook.
 * @example
 * const showToast = useToast()
 * <Button onClick={() => showToast({header: 'Example header', body: 'Example body'})}
 * >Click me
 * </Button>
 */
export function Toast({ variant, heading, body }: ToastProps) {
  return (
    <div
      className={classNames(
        'font-public-sans flex w-full flex-col gap-2 border-l-8 p-5',
        {
          'bg-state-success-lighter border-l-state-success':
            variant === 'success',
          'bg-state-error-lighter border-l-state-error': variant === 'error',
        }
      )}
    >
      <div className="flex gap-1">
        {variant === 'success' ? <CircleCheckIcon /> : <ExclamationPointIcon />}
        {heading ? (
          <h4 className="ml-2 text-2xl font-bold text-black">{heading}</h4>
        ) : null}
      </div>
      <p className="ml-11 leading-[1.6rem] text-black">{body}</p>
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

function ExclamationPointIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      className="shrink-0"
    >
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
    </svg>
  );
}

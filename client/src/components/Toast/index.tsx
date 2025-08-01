import { Icon } from '@trussworks/react-uswds';

type ToastProps = {
  heading?: string;
  body?: string;
};

/**
 * Don't use `Toast` directly. Instead use the `useToast` hook.
 * @example
 * const showToast = useToast()
 * <Button onClick={() => showToast({header: 'Example header', body: 'Example body'})}
 * >Click me
 * </Button>
 */
export function Toast({ heading, body }: ToastProps) {
  return (
    <div className="usa-alert usa-alert--success flex h-full w-full items-center">
      <div className="flex w-full flex-row items-start gap-4 p-2">
        <Icon.CheckCircle aria-hidden size={4} className="flex-shrink-0" />
        <div className="flex w-full flex-col gap-2 overflow-hidden">
          <h4 className="font-public-sans truncate overflow-hidden text-xl font-bold whitespace-nowrap">
            {heading}
          </h4>
          {body ? (
            <p className="font-public-sans truncate overflow-hidden whitespace-nowrap">
              {body}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

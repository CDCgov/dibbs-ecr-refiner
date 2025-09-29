import { Alert, AlertProps, HeadingLevel } from '@trussworks/react-uswds';

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
    <Alert
      className="w-full"
      type={variant}
      heading={
        heading ? (
          <span className={`usa-alert__heading ml-8 text-lg font-bold`}>
            {heading}
          </span>
        ) : null
      }
      headingLevel={heading ? headingLevel : 'h4'}
    >
      {body}
    </Alert>
  );
}

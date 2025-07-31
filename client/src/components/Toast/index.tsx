import { Alert, HeadingLevel } from '@trussworks/react-uswds';
import { toast, ToastOptions } from 'react-toastify';
import classNames from 'classnames';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

type ToastProps = {
  toastVariant: AlertType;
  heading?: string;
  body: string;
  headingLevel?: HeadingLevel;
  hideProgressBar?: boolean;
};

const Toast: React.FC<ToastProps> = ({
  toastVariant,
  heading,
  body,
  headingLevel = 'h4',
}) => {
  return (
    <Alert
      type={toastVariant}
      heading={
        heading ? (
          <span className={`usa-alert__heading ${headingLevel}`}>
            {heading}
          </span>
        ) : undefined
      }
      headingLevel={heading ? headingLevel : 'h4'}
    >
      {body}
    </Alert>
  );
};

const options: ToastOptions = {
  // uncomment this to debug toast styling issues
  // progress: 0.2,
  hideProgressBar: false,
  position: 'bottom-left',
  closeOnClick: true,
  closeButton: false,
  className: classNames('!p-0', '!mt-0'),
  pauseOnFocusLoss: false,
};

export function showToastConfirmation(content: {
  body: string;
  heading?: string;
  variant?: AlertType;
  headingLevel?: HeadingLevel;
  duration?: number;
  hideProgressBar?: boolean;
}) {
  const toastVariant = content.variant ?? 'success';
  const toastDuration = content.duration ?? 5000; // Default to 5000ms
  const hideProgressBar = content.hideProgressBar ?? false;

  toast[toastVariant](
    <Toast
      toastVariant={toastVariant}
      heading={content.heading}
      headingLevel={content.headingLevel}
      body={content.body ?? ''}
    />,
    { ...options, autoClose: toastDuration, hideProgressBar: hideProgressBar }
  );
}

export default Toast;

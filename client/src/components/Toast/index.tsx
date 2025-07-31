import { HeadingLevel, Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { toast, ToastOptions } from 'react-toastify';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

type ToastProps = {
  toastVariant: AlertType;
  heading?: string;
  body: string;
  headingLevel?: HeadingLevel;
  hideProgressBar?: boolean;
};

const Toast: React.FC<ToastProps> = ({ heading, body }) => {
  return (
    <div className="usa-alert usa-alert--success w-full">
      <div className="flex flex-row items-start gap-4 p-2">
        <Icon.CheckCircle aria-hidden size={4} />
        <div className="flex flex-col gap-2">
          <h4 className="font-public-sans text-xl font-bold">{heading}</h4>
          <p className="font-public-sans">{body}</p>
        </div>
      </div>
    </div>
  );
};

const globalOptions: ToastOptions = {
  // uncomment this to debug toast styling issues
  // progress: 0.2,
  hideProgressBar: false,
  position: 'bottom-left',
  closeOnClick: true,
  closeButton: false,
  className: classNames('!p-0', '!m-0'),
  pauseOnFocusLoss: false,
  pauseOnHover: true,
};

export function useToast(options: {
  body: string;
  heading?: string;
  variant?: AlertType;
  headingLevel?: HeadingLevel;
  duration?: number;
  hideProgressBar?: boolean;
}) {
  const { body, variant, heading, duration, hideProgressBar, headingLevel } =
    options;

  return () =>
    toast(
      <Toast
        body={body ?? ''}
        toastVariant={variant ?? 'success'}
        heading={heading}
        headingLevel={headingLevel}
      />,
      {
        ...globalOptions,
        autoClose: duration ?? 5000,
        hideProgressBar: hideProgressBar ?? false,
      }
    );
}

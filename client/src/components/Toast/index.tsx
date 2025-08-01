import { HeadingLevel, Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { toast, ToastOptions } from 'react-toastify';

type ToastProps = {
  heading?: string;
  body?: string;
  headingLevel?: HeadingLevel;
  hideProgressBar?: boolean;
};

const Toast: React.FC<ToastProps> = ({ heading, body }) => {
  return (
    <div className="usa-alert usa-alert--success flex h-full w-full items-center">
      <div className="flex flex-row items-start gap-4 p-2">
        <Icon.CheckCircle aria-hidden size={4} />
        <div className="flex flex-col gap-2">
          <h4 className="font-public-sans text-xl font-bold">{heading}</h4>
          {body ? <p className="font-public-sans">{body}</p> : null}
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
  className: classNames(
    '!p-0',
    '!m-0',
    '!w-[26.25rem]',
    '!h-[4.5rem]',
    '!bg-state-success-lighter',
    '!items-center'
  ),
  pauseOnFocusLoss: false,
  pauseOnHover: true,
};

export function useToast(options: {
  body?: string;
  heading?: string;
  headingLevel?: HeadingLevel;
  duration?: number;
  hideProgressBar?: boolean;
}) {
  const { body, heading, duration, hideProgressBar, headingLevel } = options;

  return () =>
    toast(
      <Toast body={body ?? ''} heading={heading} headingLevel={headingLevel} />,
      {
        ...globalOptions,
        autoClose: duration ?? 5000,
        hideProgressBar: hideProgressBar ?? false,
      }
    );
}

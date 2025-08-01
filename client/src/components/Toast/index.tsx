import { HeadingLevel, Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { toast, ToastOptions } from 'react-toastify';

type ToastProps = {
  heading?: string;
  body?: string;
  headingLevel?: HeadingLevel;
  hideProgressBar?: boolean;
};

function Toast({ heading, body }: ToastProps) {
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

export function useToast() {
  return (options: {
    body?: string;
    heading?: string;
    headingLevel?: HeadingLevel;
    duration?: number;
    hideProgressBar?: boolean;
  }) =>
    toast(
      <Toast
        body={options.body ?? ''}
        heading={options.heading}
        headingLevel={options.headingLevel}
      />,
      {
        ...globalOptions,
        autoClose: options.duration ?? 5000,
        hideProgressBar: options.hideProgressBar ?? false,
      }
    );
}

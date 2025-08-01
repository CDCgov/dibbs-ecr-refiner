import { HeadingLevel } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { toast, ToastOptions } from 'react-toastify';
import { Toast } from '../components/Toast';

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

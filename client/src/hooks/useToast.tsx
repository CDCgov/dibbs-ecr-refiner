import classNames from 'classnames';
import { toast, ToastOptions } from 'react-toastify';
import { Toast } from '../components/Toast';

const defaultToastWidthInRem = 45;

const globalOptions: ToastOptions = {
  // uncomment this to debug toast styling issues
  // progress: 0.2,
  position: 'bottom-left',
  closeOnClick: true,
  closeButton: false,
  className: classNames(
    '!p-0',
    '!h-[4.5rem]',
    '!max-w-4/5',
    '!items-center',
    'rounded-md'
  ),
  pauseOnFocusLoss: false,
  pauseOnHover: true,
};

export function useToast() {
  return (options: {
    body?: string;
    heading?: string;
    variant?: 'success' | 'error';
    duration?: number;
    hideProgressBar?: boolean;
  }) => {
    const { body, heading, variant, duration, hideProgressBar } = options;

    const defaultedVariant = variant ?? 'success';
    const toastDefaultWiderThanViewPort =
      window.innerWidth <= defaultToastWidthInRem * 16;

    toast(
      <Toast
        body={body ?? ''}
        heading={heading ?? ''}
        variant={defaultedVariant}
      />,
      {
        ...globalOptions,
        theme: defaultedVariant === 'success' ? 'light' : 'dark',
        autoClose: duration ?? 5000,
        hideProgressBar:
          (hideProgressBar || toastDefaultWiderThanViewPort) ?? false,
        className: classNames(globalOptions.className, {
          '!bg-state-success-lighter': defaultedVariant === 'success',
          '!bg-state-error': defaultedVariant === 'error',
        }),
      }
    );
  };
}

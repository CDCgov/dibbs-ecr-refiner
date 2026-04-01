import { Input as HeadlessUiInput, InputProps } from '@headlessui/react';
import classNames from 'classnames';

function Input({ className, ...props }: InputProps) {
  return <HeadlessUiInput className={classNames(className)} {...props} />;
}

export { Input, type InputProps };

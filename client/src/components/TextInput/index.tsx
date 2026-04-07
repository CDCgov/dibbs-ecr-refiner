import { Input, InputProps } from '@headlessui/react';
import classNames from 'classnames';

function TextInput({ className, ...props }: InputProps) {
  return (
    <Input
      className={classNames(
        'p-2 outline -outline-offset-1 outline-gray-600',
        className
      )}
      {...props}
    />
  );
}

export { TextInput, type InputProps as TextInputProps };

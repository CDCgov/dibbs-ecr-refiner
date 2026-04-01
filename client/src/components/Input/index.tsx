import { Input as HeadlessUiInput, InputProps } from '@headlessui/react';

function Input({ ...props }: InputProps) {
  return <HeadlessUiInput {...props} />;
}

export { Input, type InputProps };

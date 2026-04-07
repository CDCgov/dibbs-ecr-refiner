import { Field as HeadlessField, FieldProps } from '@headlessui/react';
import classNames from 'classnames';

function Field({ className, ...props }: FieldProps) {
  return (
    <HeadlessField
      className={classNames('flex flex-col gap-2', className)}
      {...props}
    />
  );
}

export { Field, type FieldProps };

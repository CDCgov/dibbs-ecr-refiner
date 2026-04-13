import {
  Combobox as HeadlessCombobox,
  ComboboxProps,
  ComboboxInput as HeadlessInput,
  ComboboxButton as HeadlessButton,
  ComboboxOptions as HeadlessOptions,
  ComboboxOption as HeadlessOption,
  ComboboxOptionsProps,
  ComboboxOptionProps,
  ComboboxInputProps,
} from '@headlessui/react';
import classNames from 'classnames';

function Combobox<TValue, TMultiple extends boolean | undefined = undefined>({
  value,
  onChange,
  onClose,
  children,
  ...props
}: ComboboxProps<TValue, TMultiple>) {
  return (
    <HeadlessCombobox
      value={value}
      onChange={onChange}
      onClose={onClose}
      {...props}
    >
      {children}
    </HeadlessCombobox>
  );
}

function ComboboxInput<T>({
  className,
  ...props
}: ComboboxInputProps<'input', T>) {
  return (
    <div className="relative">
      <HeadlessInput
        className={classNames(
          'w-full border border-[#565c65] bg-white py-2 pr-10 pl-2',
          'text-gray-90 text-base',
          'data-open:focus:outline-none!',
          className
        )}
        {...props}
      />
      <HeadlessButton className="absolute inset-y-0 right-0 flex w-10 cursor-pointer items-center justify-center">
        <span className="border-t-gray-90 border-x-[5px] border-t-[6px] border-x-transparent" />
      </HeadlessButton>
    </div>
  );
}

function ComboboxOptions({
  children,
  className,
  ...props
}: ComboboxOptionsProps) {
  return (
    <HeadlessOptions
      portal
      anchor="bottom start"
      transition
      className={classNames(
        'z-50 w-(--input-width) border border-[#565c65] bg-white empty:invisible',
        'max-h-64 overflow-y-auto',
        'transition duration-100 ease-in data-leave:data-closed:opacity-0',
        className
      )}
      {...props}
    >
      {children}
    </HeadlessOptions>
  );
}

function ComboboxOption<T>({
  children,
  className,
  ...props
}: ComboboxOptionProps<'li', T>) {
  return (
    <HeadlessOption
      className={classNames(
        'text-gray-90 border-gray-10 flex w-full cursor-default items-center border-b px-2 py-2 text-base select-none',
        'hover:ring-blue-40v data-focus:ring-blue-40v hover:ring-4 data-focus:ring-4 data-focus:ring-inset',
        className
      )}
      {...props}
    >
      {(bag) => (
        <span className={bag.selected ? 'ml-0' : 'ml-6'}>
          {typeof children === 'function' ? children(bag) : children}
        </span>
      )}
    </HeadlessOption>
  );
}

export { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption };

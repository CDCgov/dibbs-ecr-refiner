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
          'text-gray-90',
          'data-open:focus:outline-none!',
          className
        )}
        onClick={(e) => {
          // this opens the menu on input click similar to the way USWDS Combobox component works
          const isOpen =
            e.currentTarget.getAttribute('aria-expanded') === 'true';
          if (!isOpen) {
            const button = e.currentTarget
              .closest('.relative')
              ?.querySelector('button');
            button?.click();
          }
        }}
        {...props}
      />
      <HeadlessButton className="absolute inset-y-0 right-0 flex w-10 cursor-pointer items-center justify-center">
        <ArrowDown />
      </HeadlessButton>
    </div>
  );
}

function ArrowDown() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="grey"
    >
      <path d="M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z" />
    </svg>
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
        'max-h-52! overflow-y-auto',
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
        'text-gray-90 border-gray-10 flex w-full cursor-pointer items-center border-b px-2 py-2 select-none',
        'hover:ring-blue-40v data-focus:ring-blue-40v hover:ring-4 data-focus:ring-4 data-focus:ring-inset',
        className
      )}
      {...props}
    >
      {(bag) => (
        <span>{typeof children === 'function' ? children(bag) : children}</span>
      )}
    </HeadlessOption>
  );
}

export { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption };

import {
  Combobox as HeadlessCombobox,
  ComboboxInput as HeadlessInput,
  ComboboxButton as HeadlessButton,
  ComboboxOptions as HeadlessOptions,
  ComboboxOption as HeadlessOption,
  ComboboxProps,
  ComboboxOptionsProps,
  ComboboxOptionProps,
  ComboboxInputProps,
  Button,
} from '@headlessui/react';
import classNames from 'classnames';
import { useRef } from 'react';

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
  onClear,
  hasValue,
  ...props
}: ComboboxInputProps<'input', T> & {
  onClear?: () => void;
  hasValue?: boolean;
}) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative">
      <HeadlessInput
        ref={inputRef}
        className={classNames(
          'w-full border py-2 pl-2',
          { 'pr-20': hasValue },
          { 'pr-10': !hasValue },
          'text-gray-90 border-gray-cool-60 bg-white',
          'data-open:focus:outline-none!',
          className
        )}
        onClick={(e) => {
          const isOpen =
            e.currentTarget.getAttribute('aria-expanded') === 'true';
          if (!isOpen) buttonRef.current?.click();
        }}
        {...props}
      />
      <div className="absolute inset-y-0 right-0 flex">
        {hasValue && onClear && (
          <Button
            type="button"
            aria-label="Clear selection"
            className="flex w-10 cursor-pointer items-center justify-center"
            onClick={(e) => {
              e.stopPropagation();
              onClear();
              inputRef.current?.focus();
            }}
          >
            <XIcon />
          </Button>
        )}
        <HeadlessButton
          ref={buttonRef}
          aria-label="Open the condition dropdown menu"
          className="flex w-10 cursor-pointer items-center justify-center"
        >
          <ArrowDown />
        </HeadlessButton>
      </div>
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
      fill="gray"
    >
      <path d="M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="gray"
    >
      <path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
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
        'z-50 max-h-52! w-(--input-width) overflow-y-auto border',
        'border-gray-cool-60 bg-white',
        'transition duration-100 ease-in empty:invisible data-leave:data-closed:opacity-0',
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
        'flex w-full cursor-pointer items-center border-b px-2 py-2 select-none',
        'text-gray-90 border-gray-10',
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

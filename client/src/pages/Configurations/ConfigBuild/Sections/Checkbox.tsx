import { Checkbox as HeadlessCheckbox, CheckboxProps } from '@headlessui/react';

export function Checkbox({ ...props }: CheckboxProps) {
  return (
    <HeadlessCheckbox
      className="group block size-5 cursor-pointer rounded border bg-white data-checked:bg-blue-500 data-disabled:cursor-not-allowed data-disabled:opacity-50 data-checked:data-disabled:bg-gray-500"
      {...props}
    >
      <svg
        className="group-data-checked:bg-blue-cool-50 hidden stroke-white group-data-checked:block"
        viewBox="0 0 14 14"
        fill="none"
      >
        <path
          d="M3 8L6 11L11 3.5"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </HeadlessCheckbox>
  );
}

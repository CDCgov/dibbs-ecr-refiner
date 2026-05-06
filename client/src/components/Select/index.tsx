import { Select as HeadlessSelect, SelectProps } from '@headlessui/react';
import classNames from 'classnames';

interface SelectContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function SelectContainer({ children, className }: SelectContainerProps) {
  return (
    <div className={classNames('w-full max-w-lg', className)}>{children}</div>
  );
}

export function Select({ children, className, ...props }: SelectProps) {
  return (
    <div className="relative">
      <HeadlessSelect
        className={classNames(
          'border-gray-cool-60 w-full appearance-none border bg-white px-2 py-2.5 text-black',
          'outline-black focus:not-data-focus:outline-none data-focus:outline-2 data-focus:-outline-offset-2',
          className
        )}
        {...props}
      >
        {children}
      </HeadlessSelect>
      <ArrowsIcon />
    </div>
  );
}

function ArrowsIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      className="group pointer-events-none absolute top-1/2 right-2.5 size-5 -translate-y-1/2"
      aria-hidden="true"
    >
      <path d="M12 5.83 15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zm0 12.34L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17z" />
    </svg>
  );
}

import { Input, InputProps } from '@headlessui/react';
import classNames from 'classnames';

type SearchProps = Omit<InputProps, 'type'>;

export function Search({
  placeholder = 'Search',
  className,
  ...props
}: SearchProps) {
  return (
    <div
      className={classNames(
        'has-[input:focus-within]:outline-blue-40v flex w-full max-w-120 items-center gap-2 rounded-md bg-white p-1 pl-3 outline-1 -outline-offset-1 outline-gray-600 has-[input:focus-within]:outline-5 has-[input:focus-within]:-outline-offset-2',
        className
      )}
    >
      <SearchIcon />
      <Input
        className="font-public-sans h-4 w-full text-base leading-5 font-normal text-gray-500 focus:outline-none!"
        placeholder={placeholder}
        type="search"
        {...props}
      />
    </div>
  );
}

function SearchIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15.5 14H14.71L14.43 13.73C15.41 12.59 16 11.11 16 9.5C16 5.91 13.09 3 9.5 3C5.91 3 3 5.91 3 9.5C3 13.09 5.91 16 9.5 16C11.11 16 12.59 15.41 13.73 14.43L14 14.71V15.5L19 20.49L20.49 19L15.5 14ZM9.5 14C7.01 14 5 11.99 5 9.5C5 7.01 7.01 5 9.5 5C11.99 5 14 7.01 14 9.5C14 11.99 11.99 14 9.5 14Z"
        fill="#919191"
      />
    </svg>
  );
}

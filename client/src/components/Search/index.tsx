import { Input, InputProps } from '../Input';
import SearchSvg from '../../assets/sprite.svg';
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
        'has-[input:focus-within]:outline-blue-40v flex w-full max-w-120 items-center gap-2 rounded-md bg-white/5 p-1 pl-3 outline-1 -outline-offset-1 outline-gray-600 has-[input:focus-within]:outline-5 has-[input:focus-within]:-outline-offset-2',
        className
      )}
    >
      <SearchIcon />
      <Input
        className="font-public-sans h-4 w-full text-base leading-5 font-normal focus:outline-none!"
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
      fontSize={24}
      color="#919191"
      aria-hidden="true"
      role="img"
      focusable="false"
      className="usa-icon"
    >
      <use href={`${SearchSvg}#search`}></use>
    </svg>
  );
}

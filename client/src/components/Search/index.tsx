import {
  InputPrefix,
  InputGroup,
  TextInput,
  TextInputProps,
} from '@trussworks/react-uswds';

import SearchSvg from '../../assets/sprite.svg';

type SearchProps = Omit<TextInputProps, 'type'>;

export function Search({ placeholder = 'Search', ...props }: SearchProps) {
  return (
    <InputGroup className="!border-gray-cool-40 !m-0 !rounded-sm bg-white">
      <InputPrefix>
        <SearchIcon />
      </InputPrefix>
      <TextInput
        className="!rounded-sm"
        placeholder={placeholder}
        type="search"
        {...props}
      />
    </InputGroup>
  );
}

function SearchIcon() {
  return (
    <svg aria-hidden="true" role="img" focusable="false" className="usa-icon">
      <use href={`${SearchSvg}#search`}></use>
    </svg>
  );
}

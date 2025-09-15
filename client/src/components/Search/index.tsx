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
    <InputGroup className="!m-0">
      <InputPrefix>
        <SearchIcon />
      </InputPrefix>
      <TextInput placeholder={placeholder} type="search" {...props} />
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

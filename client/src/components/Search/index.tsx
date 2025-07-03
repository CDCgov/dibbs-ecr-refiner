import {
  InputPrefix,
  InputGroup,
  TextInput,
  TextInputProps,
} from '@trussworks/react-uswds';

import SearchSvg from '../../assets/sprite.svg';

export function Search({ placeholder = 'Search' }: TextInputProps) {
  return (
    <InputGroup className="!m-0">
      <InputPrefix>
        <SearchIcon />
      </InputPrefix>
      <TextInput
        id="search"
        name="search"
        type="text"
        placeholder={placeholder}
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

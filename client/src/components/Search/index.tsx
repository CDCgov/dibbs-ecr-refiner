import { InputPrefix, InputGroup, TextInput } from '@trussworks/react-uswds';

import SearchSvg from '../../assets/sprite.svg';

interface InputPrefixProps {
  placeholder?: string;
}

export function Search({ placeholder = 'Search' }: InputPrefixProps) {
  return (
    <InputGroup className="mx-0">
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

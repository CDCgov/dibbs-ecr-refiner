import { Search } from '@components/Search';
import { useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';
import { CodeFilters } from './Filters';

interface SearchBarProps {
  filters: CodeFilters;
  setFilters: React.Dispatch<React.SetStateAction<CodeFilters>>;
}
export function SearchBar({ filters, setFilters }: SearchBarProps) {
  const DEBOUNCE_TIME_MS = 500;

  const [inputValue, setInputValue] = useState(filters.search ?? '');

  const debouncedUpdate = useDebouncedCallback((value: string) => {
    setFilters((prev) => ({ ...prev, search: value || undefined }));
  }, DEBOUNCE_TIME_MS);

  return (
    <Search
      placeholder="Search by keyword"
      className="w-70!"
      value={inputValue}
      onChange={(e) => {
        setInputValue(e.target.value);
        debouncedUpdate(e.target.value);
      }}
    />
  );
}

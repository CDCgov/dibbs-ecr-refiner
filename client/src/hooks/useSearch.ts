import { useMemo, useState } from 'react';
import Fuse, { FuseResult, IFuseOptions } from 'fuse.js';

export function useSearch<T>(
  data: T[],
  options?: IFuseOptions<T>,
  useExtendedSearch = false
) {
  const [searchText, setSearchText] = useState('');

  // Create Fuse instance only when data/options change
  const fuse = useMemo(() => {
    const searchOptions = { ...options, useExtendedSearch: useExtendedSearch };

    return new Fuse(data, searchOptions);
  }, [data, options, useExtendedSearch]);

  // Search results
  const results: FuseResult<T>[] = useMemo(() => {
    if (!searchText) return [];
    return fuse.search(searchText);
  }, [fuse, searchText]);

  return {
    searchText,
    setSearchText,
    results,
  };
}

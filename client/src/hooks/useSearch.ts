import { useMemo, useState } from 'react';
import Fuse, { FuseResult, IFuseOptions } from 'fuse.js';
import { useDebounce } from 'use-debounce';

export function useSearch<T>(
  data: T[],
  options?: IFuseOptions<T>,
  debounceMs: number = 0
) {
  const [searchText, setSearchText] = useState('');
  const [debouncedSearch] = useDebounce(searchText, debounceMs);

  const fuseOptions = useMemo(
    () => ({
      includeScore: false,
      threshold: 0.3,
      ...options,
    }),
    [options]
  );

  const fuseIndex = useMemo(() => {
    return Fuse.createIndex(fuseOptions.keys || [], data);
  }, [data, fuseOptions]);

  const fuse = useMemo(() => {
    return new Fuse(data, fuseOptions, fuseIndex);
  }, [data, fuseOptions, fuseIndex]);

  // Search results
  const results: FuseResult<T>[] = useMemo(() => {
    if (!debouncedSearch) return [];
    return fuse.search(debouncedSearch);
  }, [fuse, debouncedSearch]);

  return {
    searchText,
    setSearchText,
    results,
  };
}

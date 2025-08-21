import { useMemo, useState } from 'react';
import Fuse, { FuseResult, IFuseOptions } from 'fuse.js';

export function useSearch<T>(data: T[], options?: IFuseOptions<T>) {
  const [searchText, setSearchText] = useState('');

  // Create Fuse instance only when data/options change
  const fuse = useMemo(() => {
    return new Fuse(data, options);
  }, [data, options]);

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

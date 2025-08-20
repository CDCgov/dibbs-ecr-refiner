import { useEffect, useRef, useState } from 'react';
import type { Item } from '../fuseworker';
import type { IFuseOptions } from 'fuse.js';

type ResultsMessage = {
  type: 'results';
  results: Item[];
};

export function useWorkerSearch(
  data: Item[],
  options: IFuseOptions<Item>,
  searchText: string
) {
  const workerRef = useRef<Worker>(null);
  const [results, setResults] = useState<Item[]>([]);

  useEffect(() => {
    const worker = new Worker(new URL('../fuseWorker.ts', import.meta.url), {
      type: 'module',
    });
    workerRef.current = worker;

    worker.postMessage({ type: 'init', payload: { data, options } });

    worker.onmessage = (e: MessageEvent<ResultsMessage>) => {
      if (e.data.type === 'results') {
        setResults(e.data.results);
      }
    };

    return () => {
      worker.terminate();
    };
  }, [data, options]);

  useEffect(() => {
    if (!searchText) {
      setResults(data);
      return;
    }
    workerRef.current?.postMessage({
      type: 'search',
      payload: { query: searchText },
    });
  }, [searchText, data]);

  return results;
}

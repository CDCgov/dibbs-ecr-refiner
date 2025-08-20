import { useEffect, useRef, useState } from 'react';
import type { IFuseOptions } from 'fuse.js';
import { GetConditionCode } from '../api/schemas';

interface ResultsMessage {
  type: 'results';
  results: GetConditionCode[];
}

/**
 * Fuse.js search that runs in a web worker. This is meant to be used only for searching through
 * a condition code set since those tend to be larger data sets.
 *
 * Use the `useSearch` hook for general searching needs.
 */
export function useWorkerSearch(
  data: GetConditionCode[],
  options: IFuseOptions<GetConditionCode>,
  searchText: string
) {
  const workerRef = useRef<Worker>(null);
  const [results, setResults] = useState<GetConditionCode[]>([]);

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

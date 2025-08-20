import { useEffect, useRef, useState } from 'react';
import type { IFuseOptions } from 'fuse.js';
import { GetConditionCode } from '../api/schemas';
import { useDebouncedCallback } from 'use-debounce';

/**
 * Fuse.js search that runs in a web worker. This is meant to be used only for searching through
 * a condition code set since those tend to be larger data sets.
 *
 * Use the `useSearch` hook for general searching needs.
 */
export function useWorkerSearch(
  data: GetConditionCode[],
  options: IFuseOptions<GetConditionCode>,
  debounceMs = 200
) {
  const [results, setResults] = useState<GetConditionCode[]>([]);
  const workerRef = useRef<Worker>(null);

  useEffect(() => {
    const worker = new Worker(new URL('./fuseWorker.ts', import.meta.url), {
      type: 'module',
    });
    workerRef.current = worker;

    worker.onmessage = (e) => {
      if (e.data.type === 'results') {
        setResults(e.data.results as GetConditionCode[]);
      }
    };

    worker.postMessage({ type: 'init', payload: { data, options } });

    return () => worker.terminate();
  }, [data, options]);

  const search = useDebouncedCallback((query: string) => {
    workerRef.current?.postMessage({ type: 'search', payload: { query } });
  }, debounceMs);

  return { results, search };
}

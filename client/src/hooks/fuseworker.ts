/// <reference lib="webworker" />
import Fuse, { IFuseOptions } from 'fuse.js';
import { GetConditionCode } from '../api/schemas';

declare const self: DedicatedWorkerGlobalScope;

type InitMessage = {
  type: 'init';
  payload: {
    data: GetConditionCode[];
    options: IFuseOptions<GetConditionCode>;
  };
};

type SearchMessage = {
  type: 'search';
  payload: { query: string };
};

type WorkerMessage = InitMessage | SearchMessage;

let fuse: Fuse<GetConditionCode> | null = null;

self.onmessage = (e: MessageEvent<WorkerMessage>) => {
  const { type, payload } = e.data;

  switch (type) {
    case 'init':
      fuse = new Fuse(payload.data, payload.options);
      break;

    case 'search':
      if (!fuse) {
        self.postMessage({ type: 'results', results: [] });
        return;
      }
      self.postMessage({
        type: 'results',
        results: fuse.search(payload.query).map((r) => r.item),
      });
      break;
  }
};

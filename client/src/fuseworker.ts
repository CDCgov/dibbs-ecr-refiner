/// <reference lib="webworker" />
import Fuse, { IFuseOptions } from 'fuse.js';

declare const self: DedicatedWorkerGlobalScope;

export type Item = { code: string; description: string; system: string };

type InitMessage = {
  type: 'init';
  payload: { data: Item[]; options: IFuseOptions<Item> };
};

type SearchMessage = {
  type: 'search';
  payload: { query: string };
};

type WorkerMessage = InitMessage | SearchMessage;

let fuse: Fuse<Item> | null = null;

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

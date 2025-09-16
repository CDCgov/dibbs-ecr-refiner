/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GIT_HASH: string | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// orval.config.ts

import { defineConfig } from 'orval';

export default defineConfig({
  fastapi: {
    input: '/app/shared/openapi.json',
    output: {
      mode: 'tags-split',
      target: './src/api', // react hook output
      schemas: './src/api/schemas',
      client: 'react-query',
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
});

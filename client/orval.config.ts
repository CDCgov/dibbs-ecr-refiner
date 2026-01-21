import { defineConfig } from 'orval';

export default defineConfig({
  fastapi: {
    input: {
      target: '/app/shared/openapi.json',
      filters: {
        mode: 'exclude',
        tags: ['internal'],
      },
    },
    output: {
      mode: 'tags-split',
      target: './src/api', // react hook output
      schemas: './src/api/schemas',
      client: 'react-query',
      httpClient: 'axios',
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
});

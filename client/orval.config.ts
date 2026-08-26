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
      override: {
        header: false,
        operations: {
          // We need to generate an infinite hook for `useGetCodes`
          // to support the "Manage codes" feature
          getCodes: {
            query: {
              useInfinite: true,
              useInfiniteQueryParam: 'cursor',
            },
          },
        },
      },
    },
    hooks: {
      afterAllFilesWrite:
        'prettier --write && node ../.justscripts/js/clean-trailing-newlines.js',
    },
  },
});

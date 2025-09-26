# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config({
  extends: [
    // Remove ...tseslint.configs.recommended and replace with this
    ...tseslint.configs.recommendedTypeChecked,
    // Alternatively, use this for stricter rules
    ...tseslint.configs.strictTypeChecked,
    // Optionally, add this for stylistic rules
    ...tseslint.configs.stylisticTypeChecked,
  ],
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
});
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x';
import reactDom from 'eslint-plugin-react-dom';

export default tseslint.config({
  plugins: {
    // Add the react-x and react-dom plugins
    'react-x': reactX,
    'react-dom': reactDom,
  },
  rules: {
    // other rules...
    // Enable its recommended typescript rules
    ...reactX.configs['recommended-typescript'].rules,
    ...reactDom.configs.recommended.rules,
  },
});
```

## Generated Data Fetching Hooks

This project uses a variety of tools in order to automatically generate [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview) hooks that can be used from the React client to interact with the FastAPI server. Automatically generating hooks to interact with the server means that developers will not need to create (or modify) these hooks each time a route is added (or updated) in the FastAPI. Another benefit of code generation is that types will always remain consistent across the client and server. Without code generation, developers would need to manually ensure these types don't drift from one another.

### How it works

1. During local development FastAPI writes a [refiner/openapi.json file](/refiner/openapi.json) any time the server is modified
2. The [docker-compose.yml file](/docker-compose.yaml) used for local development starts the `client` container with `npm run dev`
3. `npm run dev` uses [concurrently](https://www.npmjs.com/package/concurrently) to run two scripts at once: `watch:openapi`, which uses [nodemon](https://www.npmjs.com/package/nodemon) to monitor changes to the `refiner/openapi.json` file, and `vite`, which starts the dev server
4. When `refiner/openapi.json` is modified, nodemon will run `npm run codegen` (defined in [nodemon's config file](/client/nodemon.json))
5. The codegen script runs `orval` (using its [config file](/client/orval.config.ts)) to generate the TanStack Query hooks
6. All of the generated files with the hooks will get dropped into the `client/src/api` directory.

> [!NOTE]
> Files located in `client/src/api` should never be modified manually. Orval will continuously be updating these files as the Python codebase changes over time.

### Requirements

There are a few things that must be done when creating a new API route in order to get the best results from code generation.

When creating a new handler on the server we want to ensure we add the following:

- `response_model`: This tells the client how to generate TypeScript types
- `tag`: This will allow us to exclude handlers from codegen, such as handlers tagged `internal`. This may make sense for "internal" tasks like a `/healthcheck` where there is no need for the client to interact with this route
- `operation_id`: This is a friendly name that will be used for the hook. For example, if I give my `/configurations` route an `operation_id` of `getConfigurations` then my React hook to query this endpoint will be called `useGetConfigurations`

### Excluding FastAPI Routes from Hook Generation

If you are working on a route that may not need to be queried directly by the client, you can mark the route as "internal" by tagging it as such.

```python
@router.get("/healthcheck", tags=["internal"])
```

With the `internal` tag included, hook generation will be skipped.

### Usage

Continuing from the example above, the `useGetConfigurations` hook will be generated (or updated) and placed in the `client/src/api/configurations/configurations.ts` file. It can be used within a React component like this:

```tsx
function MyPage() {
  const { data, isPending, isError } = useGetConfigurations();

  if (isPending) return 'Loading...';
  if (isError) return 'Error occurred!';

  return <div>{data.data.length === 0 ? 'No data' : data.data[0].name}</div>;
}
```

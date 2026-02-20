/**
 * Gets the `app-env` variable from `index.html` inserted dynamically by the server
 * during a request.
 * @returns the environment in which the app is running (`local`, `demo`, `prod`, etc.)
 */
export function useGetEnv(): 'local' | 'live' {
  const placeholder = '%APP_ENV%'.toLowerCase(); // see `serve_index` server middleware
  const env = document
    .querySelector('meta[name="app-env"]')
    ?.getAttribute('content')
    ?.toLowerCase();

  if (!env) {
    console.error('No environment found in index.html.');
    return 'live';
  }

  if (env === placeholder || env === 'local') return 'local';

  return 'live';
}

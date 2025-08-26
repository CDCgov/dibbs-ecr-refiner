/**
 * Gets the `app-env` variable from `index.html` inserted dynamically inserted by the server
 * during a request.
 * @returns the environment in which the app is running (`local`, `demo`, `prod`, etc.)
 */
export function useGetEnv(): string {
  const env = document
    .querySelector('meta[name="app-env"]')
    ?.getAttribute('content');

  if (!env) {
    console.error('No environment found in index.html.');
  }

  return env?.toLowerCase() ?? 'local';
}

/**
 * Gets the `app-env` variable from `index.html` inserted dynamically inserted by the server
 * during a request.
 * @returns the environment in which the app is running (`local`, `demo`, `prod`, etc.)
 */
export function useGetEnv(): 'local' | 'demo' | 'prod' {
  const env = document
    .querySelector('meta[name="app-env"]')
    ?.getAttribute('content')
    ?.toLowerCase();

  if (!env) {
    console.error('No environment found in index.html.');
    return 'local';
  }

  console.log('SELECTEDENV', env);

  if (env === 'prod') {
    return 'prod';
  } else if (env === 'demo') {
    return 'demo';
  } else {
    return 'local';
  }
}

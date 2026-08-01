import { useLocation } from 'react-router';

/**
 * Uses the URL to determine which 'step' of the configuration is being viewed.
 * @returns The 'step' of a configuration currently being viewed (`manage-codes`, `test`, etc.)
 */
export function useGetStep() {
  const { pathname } = useLocation();
  return pathname.split('/').slice(-1)[0];
}

import { useEffect } from 'react';

/**
 * Hook to manage configuration lock acquisition and release.
 *
 * This hook acquires/refreshes the lock on mount and schedules release on unmount.
 * The schedule/cancel pattern ensures that StrictMode double-invoke and SPA navigation
 * between build/activate views do not prematurely drop the lock.
 *
 * On mount: fires-and-forgets acquire-lock POST
 * On unmount: schedules release-lock beacon after 150ms delay
 * On remount (before delay expires): cancels pending release
 */
const pendingReleases = new Map<string, ReturnType<typeof setTimeout>>();

export function useConfigLock(id?: string) {
  useEffect(() => {
    if (!id) return;

    // Cancel any pending release scheduled by a just-unmounted instance
    // This handles StrictMode double-invoke and SPA route changes
    if (pendingReleases.has(id)) {
      clearTimeout(pendingReleases.get(id));
      pendingReleases.delete(id);
    }

    // Acquire/refresh lock on mount
    void fetch(`/api/v1/configurations/${id}/acquire-lock`, {
      method: 'POST',
    });

    // Release lock on beforeunload via sendBeacon
    const releaseLock = () => {
      navigator.sendBeacon(`/api/v1/configurations/${id}/release-lock`);
    };

    window.addEventListener('beforeunload', releaseLock);

    return () => {
      window.removeEventListener('beforeunload', releaseLock);
      // Schedule release with delay to allow for StrictMode remount
      const timer = setTimeout(() => {
        releaseLock();
        pendingReleases.delete(id);
      }, 150);
      pendingReleases.set(id, timer);
    };
  }, [id]);
}

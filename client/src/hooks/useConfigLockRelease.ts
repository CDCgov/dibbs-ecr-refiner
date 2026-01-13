import { useEffect } from 'react';

export function useConfigLockRelease(id?: string) {
  useEffect(() => {
    if (!id) return;

    const releaseLock = () => {
      navigator.sendBeacon(`/api/v1/configurations/${id}/release-lock`);
    };

    window.addEventListener('beforeunload', releaseLock);

    return () => {
      window.removeEventListener('beforeunload', releaseLock);
      releaseLock();
    };
  }, [id]);
}

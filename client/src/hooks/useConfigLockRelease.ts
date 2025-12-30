import { useEffect } from 'react';

/**
 * @description Release config lock on beforeunload.
 * Usage: useConfigLockRelease(id:string)
 */
export function useConfigLockRelease(id?: string) {
  useEffect(() => {
    if (!id) return;
    type DidMountRef = { current: boolean };
    const win = window as unknown as {
      _didMount_ref_configLockRelease?: DidMountRef;
    };
    const didMount: DidMountRef = win._didMount_ref_configLockRelease || {
      current: false,
    };
    if (!win._didMount_ref_configLockRelease)
      win._didMount_ref_configLockRelease = didMount;
    if (!didMount.current) {
      didMount.current = true;
      return;
    }
    const handleReleaseLock = () => {
      const url = `/api/v1/configurations/${id}/release-lock`;
      navigator.sendBeacon(url);
    };
    window.addEventListener('beforeunload', handleReleaseLock);
    return () => {
      handleReleaseLock();
      window.removeEventListener('beforeunload', handleReleaseLock);
    };
  }, [id]);
}

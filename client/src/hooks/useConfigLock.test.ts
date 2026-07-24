import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useConfigLock } from './useConfigLock';

describe('useConfigLock', () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  let sendBeaconMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();

    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    sendBeaconMock = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, 'sendBeacon', {
      writable: true,
      value: sendBeaconMock,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllTimers();
    vi.unstubAllGlobals();
  });

  it('fires acquire POST to correct URL on mount', () => {
    const configId = 'test-config-123';

    renderHook(() => useConfigLock(configId));

    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/configurations/${configId}/acquire-lock`,
      { method: 'POST' }
    );
  });

  it('unmount then advance timers fires sendBeacon release', () => {
    const configId = 'test-config-456';

    const { unmount } = renderHook(() => useConfigLock(configId));

    expect(sendBeaconMock).not.toHaveBeenCalled();

    unmount();

    expect(sendBeaconMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(150);

    expect(sendBeaconMock).toHaveBeenCalledWith(
      `/api/v1/configurations/${configId}/release-lock`
    );
  });

  it('unmount followed by immediate remount with same id does NOT fire release', () => {
    const configId = 'test-config-789';

    // First render
    const { unmount } = renderHook(() => useConfigLock(configId));

    expect(sendBeaconMock).not.toHaveBeenCalled();

    unmount();

    expect(sendBeaconMock).not.toHaveBeenCalled();

    // Second render with same id - should cancel pending release
    renderHook(() => useConfigLock(configId));

    vi.advanceTimersByTime(150);

    expect(sendBeaconMock).not.toHaveBeenCalled();
  });

  it('no id -> no calls', () => {
    renderHook(() => useConfigLock());

    expect(fetchMock).not.toHaveBeenCalled();
    expect(sendBeaconMock).not.toHaveBeenCalled();
  });
});

import { useGetEnv } from './useGetEnv';
import { renderHook } from '@testing-library/react';

describe('useGetEnv', () => {
  let metaTag: HTMLMetaElement | null;

  afterEach(() => {
    // Clean up meta tag after each test
    // see: index.html
    metaTag = document.querySelector('meta[name="app-env"]');
    if (metaTag) {
      metaTag.remove();
    }
  });

  it('should return `live` when the environment cannot be determined', () => {
    const { result } = renderHook(() => useGetEnv());
    expect(result.current).toBe('live');
  });

  it('should return `local` when content is the placeholder', () => {
    metaTag = document.createElement('meta');
    metaTag.name = 'app-env';
    metaTag.content = '%APP_ENV%';
    document.head.appendChild(metaTag);

    const { result } = renderHook(() => useGetEnv());
    expect(result.current).toBe('local');
  });

  it('should return `local` when content is "local"', () => {
    metaTag = document.createElement('meta');
    metaTag.name = 'app-env';
    metaTag.content = 'local';
    document.head.appendChild(metaTag);

    const { result } = renderHook(() => useGetEnv());
    expect(result.current).toBe('local');
  });

  it('should return `live` for any other environment', () => {
    metaTag = document.createElement('meta');
    metaTag.name = 'app-env';
    metaTag.content = 'prod';
    document.head.appendChild(metaTag);

    const { result } = renderHook(() => useGetEnv());
    expect(result.current).toBe('live');
  });
});

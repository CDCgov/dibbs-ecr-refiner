// @ts-nocheck
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

/**
 * Simulates index.html having this meta tag
 * <meta name="app-env" content="test" />
 *
 * Prevents console errors from being written during testing.
 */
beforeAll(() => {
  const meta = document.createElement('meta');
  meta.name = 'app-env';
  meta.content = 'test';
  document.head.appendChild(meta);
});

async function mock(mockedUri: string, stub: unknown) {
  const { Module } = (await import('module')) as unknown as {
    Module: Record<string, (uri: string, parent: unknown) => void>;
  };
  Module._load_original = Module._load;
  Module._load = (uri, parent) => {
    if (uri === mockedUri) return stub;
    return Module._load_original(uri, parent);
  };
}

vi.hoisted(async () => {
  const tabbable: typeof Tabbable = await vi.importActual('tabbable');
  return mock('tabbable', {
    ...tabbable,
    tabbable: (node: Element, options: TabbableOptions) =>
      tabbable.tabbable(node, { ...options, displayCheck: 'none' }),
    focusable: (node: Element, options: TabbableOptions) =>
      tabbable.focusable(node, { ...options, displayCheck: 'none' }),
    isTabbable: (node: Element, options: TabbableOptions) =>
      tabbable.isTabbable(node, { ...options, displayCheck: 'none' }),
    isFocusable: (node: Element, options: TabbableOptions) =>
      tabbable.isFocusable(node, { ...options, displayCheck: 'none' }),
  });
});

afterEach(() => {
  cleanup();
});

class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

(global as any).ResizeObserver = ResizeObserver;

// Mock navigator.sendBeacon for tests
Object.defineProperty(navigator, 'sendBeacon', {
  writable: true,
  value: vi.fn(),
});

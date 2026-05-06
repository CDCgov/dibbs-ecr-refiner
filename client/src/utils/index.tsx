import React from 'react';
import { FuseResultMatch } from 'fuse.js';

export function highlightMatches(
  text: string,
  matches?: readonly FuseResultMatch[],
  key?: string
): React.ReactNode {
  if (!matches || !key) return text;

  const match = matches.find((m) => m.key === key);
  if (!match || !match.indices.length) return text;

  const indices = match.indices;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  indices.forEach(([start, end], i) => {
    if (lastIndex < start) {
      parts.push(text.slice(lastIndex, start));
    }
    parts.push(<mark key={i}>{text.slice(start, end + 1)}</mark>);
    lastIndex = end + 1;
  });

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
const TWO_SECONDS_IN_MILLISECONDS = 2000;

export async function showSpinnerWithMinimalRenderDuration(
  spinnerStartRef: React.RefObject<number>,
  shouldShowSetter: React.Dispatch<boolean>,
  stopShowingSpinnerConditional: boolean,
  minimalRenderDuration = TWO_SECONDS_IN_MILLISECONDS
) {
  if (stopShowingSpinnerConditional) {
    spinnerStartRef.current = performance.now();
    shouldShowSetter(true);
  }
  if (!stopShowingSpinnerConditional && spinnerStartRef.current) {
    const spinnerEnd = performance.now();
    const spinnerDuration = spinnerEnd - spinnerStartRef.current;

    if (spinnerDuration < minimalRenderDuration) {
      // show the saving confirmation for at least desired duration so the
      // UI change registers to the user
      await sleep(minimalRenderDuration - spinnerDuration);
    }
    shouldShowSetter(false);
    spinnerStartRef.current = 0;
  }
}

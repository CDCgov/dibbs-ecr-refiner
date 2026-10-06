import React from 'react';
import { FuseResultMatch } from 'fuse.js';

// NOTE: text-gray-cool-90 applied explicitly to <mark> because browser default <mark> styling fails WCAG color-contrast; consider a shared/centralized highlight utility with design sign-off.
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
    parts.push(
      <mark key={i} className="text-gray-cool-90!">
        {text.slice(start, end + 1)}
      </mark>
    );
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

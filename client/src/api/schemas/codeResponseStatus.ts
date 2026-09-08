
export type CodeResponseStatus = typeof CodeResponseStatus[keyof typeof CodeResponseStatus];


export const CodeResponseStatus = {
  Included: 'Included',
  Excluded: 'Excluded',
} as const;

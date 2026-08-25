
export type CodeStatus = typeof CodeStatus[keyof typeof CodeStatus];


export const CodeStatus = {
  included: 'included',
  excluded: 'excluded',
} as const;

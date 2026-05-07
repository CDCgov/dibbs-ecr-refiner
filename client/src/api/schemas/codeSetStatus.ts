
export type CodeSetStatus = typeof CodeSetStatus[keyof typeof CodeSetStatus];


export const CodeSetStatus = {
  not_expanded: 'not expanded',
  partially_complete: 'partially complete',
  fully_complete: 'fully complete',
} as const;

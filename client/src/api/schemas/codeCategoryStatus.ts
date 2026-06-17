
export type CodeCategoryStatus = typeof CodeCategoryStatus[keyof typeof CodeCategoryStatus];


export const CodeCategoryStatus = {
  not_included: 'not included',
  partially_complete: 'partially complete',
  fully_complete: 'fully complete',
} as const;

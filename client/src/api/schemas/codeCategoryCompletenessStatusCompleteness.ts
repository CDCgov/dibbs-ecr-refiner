
export type CodeCategoryCompletenessStatusCompleteness = typeof CodeCategoryCompletenessStatusCompleteness[keyof typeof CodeCategoryCompletenessStatusCompleteness];


export const CodeCategoryCompletenessStatusCompleteness = {
  not_included: 'not included',
  partially_complete: 'partially complete',
  fully_complete: 'fully complete',
} as const;

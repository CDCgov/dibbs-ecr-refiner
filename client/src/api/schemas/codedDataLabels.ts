
/**
 * Enum class to type the coded data actions possible for the frontend.
 */
export const CodedDataLabelsValue = {
  retain: 'Keep original',
  refine: 'Refine',
} as const;
export type CodedDataLabels = typeof CodedDataLabelsValue;

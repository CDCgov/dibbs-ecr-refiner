
/**
 * Enum class to type the narrative actions possible for the frontend.
 */
export const CodedDataLabelsValue = {
  retain: 'Keep original',
  refine: 'Refine',
} as const;
export type CodedDataLabels = typeof CodedDataLabelsValue;

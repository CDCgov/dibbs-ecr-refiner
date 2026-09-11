
/**
 * Enum class to type the narrative actions possible for the frontend.
 */
export const NarrativeDataLabelsValue = {
  retain: 'Keep original',
  keep_on_match: 'Keep on match',
  reconstruct: 'Reconstruct',
  remove: 'Exclude',
} as const;
export type NarrativeDataLabels = typeof NarrativeDataLabelsValue;


export type NarrativeAction = typeof NarrativeAction[keyof typeof NarrativeAction];


export const NarrativeAction = {
  retain: 'retain',
  remove: 'remove',
  reconstruct: 'reconstruct',
  keep_on_match: 'keep_on_match',
} as const;

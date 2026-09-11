
export type DbNarrativeAction = typeof DbNarrativeAction[keyof typeof DbNarrativeAction];


export const DbNarrativeAction = {
  retain: 'retain',
  remove: 'remove',
  reconstruct: 'reconstruct',
  keep_on_match: 'keep_on_match',
} as const;

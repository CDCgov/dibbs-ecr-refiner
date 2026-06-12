
export type DbNarrativeAction = typeof DbNarrativeAction[keyof typeof DbNarrativeAction];


export const DbNarrativeAction = {
  retain: 'retain',
  remove: 'remove',
  reconstruct: 'reconstruct',
} as const;

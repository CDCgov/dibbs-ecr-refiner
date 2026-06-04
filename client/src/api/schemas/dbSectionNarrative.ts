
export type DbSectionNarrative = typeof DbSectionNarrative[keyof typeof DbSectionNarrative];


export const DbSectionNarrative = {
  retain: 'retain',
  remove: 'remove',
  refine: 'refine',
} as const;


export type DbSectionAction = typeof DbSectionAction[keyof typeof DbSectionAction];


export const DbSectionAction = {
  retain: 'retain',
  refine: 'refine',
} as const;

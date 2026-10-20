
export type SectionAction = typeof SectionAction[keyof typeof SectionAction];


export const SectionAction = {
  retain: 'retain',
  refine: 'refine',
} as const;

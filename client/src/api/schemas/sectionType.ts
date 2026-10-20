
export type SectionType = typeof SectionType[keyof typeof SectionType];


export const SectionType = {
  standard: 'standard',
  custom: 'custom',
} as const;

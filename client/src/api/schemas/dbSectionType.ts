
export type DbSectionType = typeof DbSectionType[keyof typeof DbSectionType];


export const DbSectionType = {
  standard: 'standard',
  custom: 'custom',
} as const;

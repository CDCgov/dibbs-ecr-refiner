
export type DbCodeResultStatus = typeof DbCodeResultStatus[keyof typeof DbCodeResultStatus];


export const DbCodeResultStatus = {
  included: 'included',
  excluded: 'excluded',
} as const;

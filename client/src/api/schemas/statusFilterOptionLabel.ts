
export type StatusFilterOptionLabel = typeof StatusFilterOptionLabel[keyof typeof StatusFilterOptionLabel];


export const StatusFilterOptionLabel = {
  Included: 'Included',
  Excluded: 'Excluded',
} as const;

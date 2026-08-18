
export type StatusFilterOptionStatus = typeof StatusFilterOptionStatus[keyof typeof StatusFilterOptionStatus];


export const StatusFilterOptionStatus = {
  included: 'included',
  excluded: 'excluded',
} as const;

import type { SetCodesStatusStatus } from './setCodesStatusStatus';

export type SetCodesStatusParams = {
update_beyond_rendered_set: boolean;
status: SetCodesStatusStatus;
search?: string | null;
code_systems?: string[];
sources?: string[];
statuses?: string[];
};

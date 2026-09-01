import type { SetCodeStatusBeyondCursorStatus } from './setCodeStatusBeyondCursorStatus';

export type SetCodeStatusBeyondCursorParams = {
status: SetCodeStatusBeyondCursorStatus;
search?: string | null;
code_systems?: string[];
sources?: string[];
statuses?: string[];
};

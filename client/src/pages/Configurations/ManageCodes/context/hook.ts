import { createContext, useContext } from 'react';
import { CodeResponse } from '../../../../api/schemas/codeResponse';

export interface CodeActionState {
  performBulkAction: boolean;
  statusChange: 'include' | 'exclude';
  selectedCodeIds: Set<string>;
  renderedTesCodes: CodeResponse[];
  renderedExcludableCodes: CodeResponse[];
  renderedCustomCodes: [];
}

export type Action =
  | {
      type: 'singleSelection';
    }
  | { type: 'bulkSelection' };

export type Dispatch = (action: Action) => void;

export const CodeManagementContext = createContext<
  { state: CodeActionState; dispatch: Dispatch } | undefined
>(undefined);

export function useSelectedCodes() {
  const context = useContext(CodeManagementContext);
  if (context === undefined) {
    throw new Error(
      'useSelectedCodes must be used within a CodeManagementProvider'
    );
  }
  return context;
}

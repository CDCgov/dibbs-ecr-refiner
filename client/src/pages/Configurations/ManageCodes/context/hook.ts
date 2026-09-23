import { createContext, useContext } from 'react';
import { CodeResponse } from '../../../../api/schemas';

export interface SelectedCodeState {
  selectedCodeIds: Set<string>;
  selectedCustomCodeIds: Set<string>;
  allSelected: boolean;
}
export interface CodeAction {
  type:
    | 'bulkInclude'
    | 'bulkExclude'
    | 'individualInclude'
    | 'individualExclude'
    | 'reset';
  selectedCodeIds?: Set<string>;
  selectedCustomCodeIds?: Set<string>;
  selectableCodes?: CodeResponse[];
}

export type Dispatch = (action: CodeAction) => void;

export const CodeManagementContext = createContext<
  { state: SelectedCodeState; dispatch: Dispatch } | undefined
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

import { createContext, useContext } from 'react';
import { CodeResponse } from '../../../../api/schemas';

type StatusChange = 'include' | 'exclude' | 'default';
export interface SelectedCodeState {
  selectedCodeIds: Set<string>;
  selectedCustomCodeIds: Set<string>;
  allSelected: boolean;
  statusChange: StatusChange;
}
export interface CodeAction {
  bulkAction: boolean;
  include: boolean;
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

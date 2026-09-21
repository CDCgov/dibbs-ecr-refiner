import { useReducer } from 'react';
import { CodeAction, CodeManagementContext, SelectedCodeState } from './hook';

function removeAll<T>(originalSet: Set<T>, toBeRemovedSet: Set<T>) {
  toBeRemovedSet.forEach((v) => originalSet.delete(v));
  return originalSet;
}

function codeActionReducer(
  codeState: SelectedCodeState,
  action: CodeAction
): SelectedCodeState {
  const renderedCodes = action.selectableCodes ?? [];
  const selectedCustomCodeIds = renderedCodes
    .filter((c) => c.is_custom)
    .map((c) => c.id);

  const selectedCodeIds = renderedCodes
    .filter((c) => !c.is_custom)
    .map((c) => c.id);

  switch (action.bulkAction) {
    case true: {
      if (action.include) {
        return {
          ...codeState,
          allSelected: action.include,
          selectedCodeIds: new Set([
            ...codeState.selectedCodeIds,
            ...selectedCodeIds,
          ]),
          selectedCustomCodeIds: new Set([
            ...codeState.selectedCustomCodeIds,
            ...selectedCustomCodeIds,
          ]),
        };
      } else {
        return {
          ...codeState,
          allSelected: action.include,
          selectedCodeIds: removeAll(
            codeState.selectedCodeIds,
            new Set(selectedCodeIds)
          ),

          selectedCustomCodeIds: removeAll(
            codeState.selectedCustomCodeIds,
            new Set(selectedCustomCodeIds)
          ),
        };
      }
    }
    case false: {
      if (action.include) {
        return {
          ...codeState,
          selectedCodeIds: action.selectedCodeIds
            ? new Set([...codeState.selectedCodeIds, ...action.selectedCodeIds])
            : codeState.selectedCodeIds,
          selectedCustomCodeIds: action.selectedCustomCodeIds
            ? new Set([
                ...codeState.selectedCustomCodeIds,
                ...action.selectedCustomCodeIds,
              ])
            : codeState.selectedCustomCodeIds,
        };
      } else {
        return {
          ...codeState,
          selectedCodeIds: action.selectedCodeIds
            ? removeAll(codeState.selectedCodeIds, action.selectedCodeIds)
            : codeState.selectedCodeIds,
          selectedCustomCodeIds: action.selectedCustomCodeIds
            ? removeAll(
                codeState.selectedCustomCodeIds,
                action.selectedCustomCodeIds
              )
            : codeState.selectedCustomCodeIds,
        };
      }
    }
  }
}

interface CodeManagementProps {
  children: React.ReactNode;
  initialCodeState: SelectedCodeState;
}
function CodeManagementProvider({
  children,
  initialCodeState,
}: CodeManagementProps) {
  const [state, dispatch] = useReducer(codeActionReducer, initialCodeState);
  const value = { state, dispatch };
  return (
    <CodeManagementContext.Provider value={value}>
      {children}
    </CodeManagementContext.Provider>
  );
}

export { CodeManagementProvider };

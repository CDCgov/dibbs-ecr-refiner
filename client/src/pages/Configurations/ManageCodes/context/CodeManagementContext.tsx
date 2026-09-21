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

  switch (action.type) {
    case 'bulkInclude': {
      return {
        allSelected: true,
        selectedCodeIds: new Set([
          ...codeState.selectedCodeIds,
          ...selectedCodeIds,
        ]),
        selectedCustomCodeIds: new Set([
          ...codeState.selectedCustomCodeIds,
          ...selectedCustomCodeIds,
        ]),
      };
    }
    case 'bulkExclude': {
      return {
        allSelected: false,
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
    case 'individualInclude': {
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
    }
    case 'individualExclude': {
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

    case 'reset': {
      return {
        allSelected: false,
        selectedCodeIds: new Set(),
        selectedCustomCodeIds: new Set(),
      };
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

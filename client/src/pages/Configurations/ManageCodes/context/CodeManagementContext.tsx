import { useReducer } from 'react';
import { Action, CodeActionState, CodeManagementContext } from './hook';

function codeActionReducer(state: CodeActionState, action: Action) {
  switch (action.type) {
    default: {
      throw new Error(`Unhandled action type: ${action.type}`);
    }
  }
}

interface CodeManagementProps {
  children: React.ReactNode;
}
function CodeManagementProvider({ children }: CodeManagementProps) {
  const [state, dispatch] = useReducer(codeActionReducer, { count: 0 });
  const value = { state, dispatch };
  return (
    <CodeManagementContext.Provider value={value}>
      {children}
    </CodeManagementContext.Provider>
  );
}

export { CodeManagementProvider };

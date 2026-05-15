import { UserResponse } from '../api/schemas';
import { useGetUser, getGetUserQueryKey } from '../api/user/user';
import { useQueryClient } from '@tanstack/react-query';

interface LoginState {
  user: UserResponse | null;
  refreshUser: () => void;
  isLoading: boolean;
}

export function useLogin(): LoginState {
  const queryClient = useQueryClient();
  const { data, isPending } = useGetUser();

  const refreshUser = () => {
    void queryClient.invalidateQueries({ queryKey: getGetUserQueryKey() });
  };

  return { user: data?.data ?? null, refreshUser, isLoading: isPending };
}

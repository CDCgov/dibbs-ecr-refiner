import { useEffect, useState } from 'react';
import { UserResponse } from '../api/schemas';

export function useLogin(): [UserResponse | null, boolean] {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function fetchUserInfo() {
      setIsLoading(true);
      try {
        const resp = await fetch('/api/user');
        if (!resp.ok) {
          setUser(null);
          setIsLoading(false);
          return;
        }

        const data = (await resp.json()) as UserResponse | null;
        if (data) {
          setUser(data);
          setIsLoading(false);
        }
      } catch {
        console.error('Network error. Please try again.');
        setUser(null);
        setIsLoading(false);
      } finally {
        setIsLoading(false);
      }
    }
    void fetchUserInfo();
  }, []);

  return [user, isLoading];
}

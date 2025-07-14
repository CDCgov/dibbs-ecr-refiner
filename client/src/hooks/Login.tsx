import { useEffect, useState } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
}

export function useLogin(): [User | null, boolean] {
  const [user, setUser] = useState<User | null>(null);
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

        const data: User = await resp.json();
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
    fetchUserInfo();
  }, []);

  return [user, isLoading];
}

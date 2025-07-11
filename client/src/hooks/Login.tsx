import { useEffect, useState } from 'react';

interface User {
  exp: number;
  iat: number;
  auth_time: number;
  jti: string;
  iss: string;
  aud: string;
  sub: string;
  typ: string;
  azp: string;
  nonce: string;
  sid: string;
  at_hash: string;
  acr: string;
  email_verified: boolean;
  name: string;
  preferred_username: string;
  given_name: string;
  family_name: string;
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

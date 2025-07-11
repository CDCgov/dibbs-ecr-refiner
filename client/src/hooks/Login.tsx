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

export function useLogin(): User | null {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    async function fetchUserInfo() {
      try {
        const resp = await fetch('/api/user');
        if (!resp.ok) {
          setUser(null);
          return;
        }

        const data: User = await resp.json();
        if (data) {
          setUser(data);
          console.log(data);
        }
      } catch {
        console.error('Network error. Please try again.');
        setUser(null);
      }
    }
    fetchUserInfo();
  }, []);

  return user;
}

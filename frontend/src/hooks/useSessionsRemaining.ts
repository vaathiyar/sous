import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/react';
import { getMe } from '@/api/user';
import type { UserMe } from '@/types';

export function useSessionsRemaining(): UserMe | null {
  const { getToken } = useAuth();
  const [data, setData] = useState<UserMe | null>(null);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) return;
      const me = await getMe(token);
      setData(me);
    })().catch(console.error);
  }, []);

  return data;
}

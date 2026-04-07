import { useState } from 'react';
import { useAuth } from '@clerk/react';
import { createSession } from '@/api/session';
import type { SessionInfo } from '@/types';

export function useStartSession() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async (recipeId: string): Promise<SessionInfo | null> => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) throw new Error('Not authenticated');
      return await createSession(recipeId, token);
    } catch {
      setError('Could not start session. Please try again.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { start, loading, error };
}

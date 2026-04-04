import { useState } from 'react';
import { createSession } from '@/api/session';
import type { SessionInfo } from '@/types';

export function useStartSession() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async (recipeId: string): Promise<SessionInfo | null> => {
    setLoading(true);
    setError(null);
    try {
      return await createSession(recipeId);
    } catch {
      setError('Could not start session. Please try again.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { start, loading, error };
}

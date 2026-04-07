import { API_BASE } from '@/config';
import type { UserMe } from '@/types';

export async function getMe(authToken: string): Promise<UserMe> {
  const res = await fetch(`${API_BASE}/api/users/me`, {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  if (!res.ok) throw new Error('Failed to fetch user');
  return res.json();
}

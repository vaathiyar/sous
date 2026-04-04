import { API_BASE } from '@/config';
import type { SessionInfo } from '@/types';

export async function createSession(recipeId: string): Promise<SessionInfo> {
  const res = await fetch(`${API_BASE}/api/voice/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId }),
  });
  if (!res.ok) throw new Error(await res.text());
  const raw = await res.json();
  return {
    ...raw,
    livekitUrl: raw.livekit_url,
    roomName: raw.room_name,
  };
}

import { API_BASE } from '@/config';
import type { Recipe, RecipeDetail } from '@/types';

export async function getRecipes(): Promise<Recipe[]> {
  const res = await fetch(`${API_BASE}/api/voice/recipes`);
  if (!res.ok) throw new Error('Failed to fetch recipes');
  return res.json();
}

export async function getRecipeDetail(id: string): Promise<RecipeDetail> {
  const res = await fetch(`${API_BASE}/api/voice/recipes/${id}`);
  if (!res.ok) throw new Error('Recipe not found');
  const raw = await res.json();
  return {
    ...raw,
    sourceUrl: raw.source_url,
    precookBriefing: raw.precook_briefing
      ? {
          ...raw.precook_briefing,
          activeTime: raw.precook_briefing.active_time,
          passiveTime: raw.precook_briefing.passive_time,
          prepItems: raw.precook_briefing.prep_items,
        }
      : null,
  };
}

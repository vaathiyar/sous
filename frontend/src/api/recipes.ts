import { API_BASE } from '@/config';
import type { Recipe, RecipeDetail } from '@/types';

export async function getRecipes(): Promise<Recipe[]> {
  const res = await fetch(`${API_BASE}/api/recipes`);
  if (!res.ok) throw new Error('Failed to fetch recipes');
  return res.json();
}

function transformRecipeDetail(raw: Record<string, unknown>): RecipeDetail {
  const briefing = raw.precook_briefing as Record<string, unknown> | null;
  return {
    ...raw as unknown as RecipeDetail,
    sourceUrl: raw.source_url as string | null,
    precookBriefing: briefing
      ? {
          ...briefing as unknown as RecipeDetail['precookBriefing'],
          activeTime: briefing.active_time as string | null,
          passiveTime: briefing.passive_time as string | null,
          prepItems: briefing.prep_items as RecipeDetail['precookBriefing']['prepItems'],
        }
      : null,
  };
}

export async function getRecipeDetail(id: string): Promise<RecipeDetail> {
  const res = await fetch(`${API_BASE}/api/recipe?id=${id}`);
  if (!res.ok) throw new Error('Recipe not found');
  return transformRecipeDetail(await res.json());
}

export async function getRecipeBySlug(slug: string): Promise<RecipeDetail> {
  const res = await fetch(`${API_BASE}/api/recipe?slug=${encodeURIComponent(slug)}`);
  if (!res.ok) throw new Error('Recipe not found');
  return transformRecipeDetail(await res.json());
}

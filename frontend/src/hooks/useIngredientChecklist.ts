import { useState } from 'react';
import type { RecipeIngredient } from '@/types';

export interface IngredientChecklist {
  checked: Set<string>;
  toggle: (name: string) => void;
  allEssentialChecked: boolean;
  progressPct: number;
  checkedCount: number;
  reset: () => void;
}

export function useIngredientChecklist(ingredients: RecipeIngredient[]): IngredientChecklist {
  const [checked, setChecked] = useState<Set<string>>(new Set());

  const toggle = (name: string) =>
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });

  const reset = () => setChecked(new Set());

  const essentialCount = ingredients.filter((i) => !i.optional).length;
  const checkedCount = checked.size;
  const allEssentialChecked =
    essentialCount > 0 &&
    ingredients.filter((i) => !i.optional && checked.has(i.name)).length === essentialCount;
  const progressPct = ingredients.length > 0 ? (checkedCount / ingredients.length) * 100 : 0;

  return { checked, toggle, allEssentialChecked, progressPct, checkedCount, reset };
}

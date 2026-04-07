export interface Recipe {
  id: string;
  slug: string;
  title: string;
  cuisine: string | null;
}

export interface SessionInfo {
  token: string;
  livekitUrl: string;
  roomName: string;
}

export interface RecipeIngredient {
  name: string;
  quantity: string | null;
  optional: boolean;
  notes: string | null;
}

export interface PrepItem {
  task: string;
  duration: string | null;
  ingredients: string[];
  notes: string | null;
}

export interface PreCookBriefing {
  summary: string;
  activeTime: string | null;
  passiveTime: string | null;
  prepItems: PrepItem[];
}

export interface RecipeDetail {
  id: string;
  slug: string;
  title: string;
  cuisine: string | null;
  sourceUrl: string | null;
  precookBriefing: PreCookBriefing | null;
  ingredients: RecipeIngredient[] | null;
}

export interface UserMe {
  sessions_used: number;
  sessions_limit: number;
}

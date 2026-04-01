import { useState, useEffect } from "react";
import RecipeListPage from "./RecipeListPage";
import RecipeDetailPage from "./RecipeDetailPage";
import VoiceSession from "./VoiceSession";
import type { Recipe, SessionInfo } from "./types";

const API_BASE = import.meta.env.VITE_BACKEND_API_URL;
if (!API_BASE) throw new Error("VITE_BACKEND_API_URL is not set");

type View = "list" | "detail" | "session";

export default function App() {
  const [view, setView] = useState<View>("list");
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selected, setSelected] = useState<Recipe | null>(null);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [sessionLoading, setSessionLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/voice/recipes`)
      .then((r) => r.json())
      .then(setRecipes)
      .catch(console.error);
  }, []);

  async function handleStartCooking() {
    if (!selected) return;
    setSessionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/voice/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_id: selected.id }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data: SessionInfo = await res.json();
      setSession(data);
      setView("session");
    } catch (e) {
      console.error(e);
    } finally {
      setSessionLoading(false);
    }
  }

  if (view === "session" && session && selected) {
    return (
      <VoiceSession
        token={session.token}
        serverUrl={session.livekit_url}
        recipeTitle={selected.title}
        onEnd={() => {
          setSession(null);
          setView("detail");
        }}
      />
    );
  }

  if (view === "detail" && selected) {
    return (
      <RecipeDetailPage
        recipeId={selected.id}
        recipeTitle={selected.title}
        onBack={() => setView("list")}
        onStartCooking={handleStartCooking}
        startLoading={sessionLoading}
      />
    );
  }

  return (
    <RecipeListPage
      recipes={recipes}
      onSelect={(recipe) => {
        setSelected(recipe);
        setView("detail");
      }}
    />
  );
}

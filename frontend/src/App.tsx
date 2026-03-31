import { useState, useEffect } from "react";
import VoiceSession from "./VoiceSession";

interface Recipe {
  id: string;
  slug: string;
  title: string;
  cuisine: string | null;
}

interface SessionInfo {
  token: string;
  livekit_url: string;
  room_name: string;
}

export default function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetch("/api/voice/recipes")
      .then((r) => r.json())
      .then(setRecipes)
      .catch(() => setError("Failed to load recipes"));
  }, []);

  async function startSession() {
    if (!selectedRecipe) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/voice/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_id: selectedRecipe.id }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSession(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (session && selectedRecipe) {
    return (
      <VoiceSession
        token={session.token}
        serverUrl={session.livekit_url}
        recipeTitle={selectedRecipe.title}
        onEnd={() => setSession(null)}
      />
    );
  }

  return (
    <div className="selector-page">
      <div className="hero">
        <span className="wordmark">Sous</span>
        <p className="tagline">Your hands-free kitchen companion</p>
      </div>

      <div className="card">
        <p className="card-label">Choose a recipe</p>

        {recipes.length === 0 && !error ? (
          <div className="empty-state">
            No recipes found.<br />
            Ingest a video first via the CLI.
          </div>
        ) : (
          <div className="select-wrap">
            <select
              className="recipe-select"
              value={selectedRecipe?.id ?? ""}
              onChange={(e) => {
                const r = recipes.find((r) => r.id === e.target.value) ?? null;
                setSelectedRecipe(r);
              }}
            >
              <option value="">— pick a recipe —</option>
              {recipes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
            <span className="select-chevron">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </span>
          </div>
        )}

        <button
          className="start-btn"
          onClick={startSession}
          disabled={!selectedRecipe || loading}
        >
          {loading ? "Starting…" : "Start Cooking Session"}
        </button>

        {error && <div className="error-msg">{error}</div>}
      </div>
    </div>
  );
}

import { useState } from 'react';
import RecipeListPage from '@/pages/RecipeListPage';
import RecipeDetailPage from '@/pages/RecipeDetailPage';
import VoiceSession from '@/pages/VoiceSession/VoiceSession';
import { useRecipes } from '@/hooks/useRecipes';
import { useStartSession } from '@/hooks/useStartSession';
import type { Recipe, SessionInfo } from '@/types';

type View = 'list' | 'detail' | 'session';

export default function App() {
  const [view, setView] = useState<View>('list');
  const [selected, setSelected] = useState<Recipe | null>(null);
  const [session, setSession] = useState<SessionInfo | null>(null);

  const { recipes } = useRecipes();
  const { start: startSession, loading: sessionLoading, error: sessionError } = useStartSession();

  const handleStartCooking = async () => {
    if (!selected) return;
    const data = await startSession(selected.id);
    if (data) {
      setSession(data);
      setView('session');
    }
  };

  if (view === 'session' && session && selected) {
    return (
      <VoiceSession
        token={session.token}
        serverUrl={session.livekitUrl}
        recipeTitle={selected.title}
        onEnd={() => {
          setSession(null);
          setView('detail');
        }}
      />
    );
  }

  if (view === 'detail' && selected) {
    return (
      <RecipeDetailPage
        recipeId={selected.id}
        recipeTitle={selected.title}
        onBack={() => setView('list')}
        onStartCooking={handleStartCooking}
        startLoading={sessionLoading}
        startError={sessionError}
      />
    );
  }

  return (
    <RecipeListPage
      recipes={recipes}
      onSelect={(recipe) => {
        setSelected(recipe);
        setView('detail');
      }}
    />
  );
}

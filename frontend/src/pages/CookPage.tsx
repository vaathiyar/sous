import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/react';
import VoiceSession from '@/pages/VoiceSession/VoiceSession';
import { getRecipeBySlug } from '@/api/recipes';
import { createSession } from '@/api/session';
import type { RecipeDetail, SessionInfo } from '@/types';
import '@/styles/CookPage.css';

type CookState =
  | { status: 'loading' }
  | { status: 'ready'; recipe: RecipeDetail; session: SessionInfo }
  | { status: 'error'; message: string; isLimit: boolean };

export default function CookPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [state, setState] = useState<CookState>({ status: 'loading' });

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;

    (async () => {
      try {
        const [recipe, token] = await Promise.all([getRecipeBySlug(slug), getToken()]);
        if (cancelled) return;
        if (!token) throw new Error('Not authenticated');
        const session = await createSession(recipe.id, token);
        if (cancelled) return;
        setState({ status: 'ready', recipe, session });
      } catch (e) {
        if (cancelled) return;
        const message = e instanceof Error ? e.message : 'Failed to start session';
        const isLimit = message.includes('limit') || message.includes('403') || message.includes('Demo');
        setState({ status: 'error', message, isLimit });
      }
    })();

    return () => { cancelled = true; };
  }, [slug]);

  if (state.status === 'loading') {
    return (
      <div className="cook-screen cook-loading">
        <span className="wordmark cook-wordmark">Suvai</span>
        <div className="cook-loading-dots">
          <span /><span /><span />
        </div>
        <p className="cook-loading-label">Preparing your session…</p>
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="cook-screen cook-error">
        <span className="wordmark cook-wordmark">Suvai</span>
        <h2 className="cook-error-title">
          {state.isLimit ? 'Demo limit reached' : 'Something went wrong'}
        </h2>
        <p className="cook-error-body">
          {state.isLimit
            ? "You've used all your demo cooking sessions."
            : state.message}
        </p>
        <button className="cook-error-btn" onClick={() => navigate(`/recipes/${slug}`)}>
          ← Back to recipe
        </button>
      </div>
    );
  }

  return (
    <VoiceSession
      token={state.session.token}
      serverUrl={state.session.livekitUrl}
      recipeTitle={state.recipe.title}
      onEnd={() => navigate(`/recipes/${slug}`)}
    />
  );
}

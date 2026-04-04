import '@/styles/RecipeListPage.css';
import type { Recipe } from '@/types';

interface RecipeListPageProps {
  recipes: Recipe[];
  onSelect: (recipe: Recipe) => void;
}

export default function RecipeListPage({ recipes, onSelect }: RecipeListPageProps) {
  return (
    <div className="list-page">
      <header className="list-header">
        <span className="wordmark">Suvai</span>
        <span className="list-header-divider" aria-hidden="true">·</span>
        <span className="list-header-sub">Your AI sous chef</span>
      </header>

      <main className="list-main">
        <div className="list-intro">
          <h1 className="list-heading">
            What shall<br />we cook?
          </h1>
          {recipes.length > 0 && (
            <p className="list-subheading">
              {recipes.length} recipe{recipes.length !== 1 ? 's' : ''} in your kitchen
            </p>
          )}
        </div>

        {recipes.length === 0 ? (
          <div className="list-empty">
            <p className="list-empty-title">The kitchen is empty.</p>
            <p className="list-empty-body">Ingest a YouTube video to get started.</p>
            <code className="list-empty-code">
              uv run python main.py ingest "&lt;youtube_url&gt;"
            </code>
          </div>
        ) : (
          <ul className="menu-list" role="list">
            {recipes.map((recipe, i) => (
              <li
                key={recipe.id}
                className="menu-item"
                style={{ animationDelay: `${i * 0.045}s` }}
              >
                <button
                  className="menu-item-btn"
                  onClick={() => onSelect(recipe)}
                >
                  <span className="menu-item-name">{recipe.title}</span>
                  <span className="menu-item-rule" aria-hidden="true" />
                  <span className="menu-item-cuisine">{recipe.cuisine ?? '—'}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </main>

      <footer className="list-footer">
        <span>Suvai — your hands-free kitchen companion</span>
      </footer>
    </div>
  );
}

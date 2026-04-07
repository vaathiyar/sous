import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '@/styles/RecipeDetailPage.css';
import { BackIcon, CheckIcon, ClockIcon } from '@/components/icons';
import { useIngredientChecklist } from '@/hooks/useIngredientChecklist';
import { getRecipeBySlug } from '@/api/recipes';
import { getYouTubeId } from '@/utils/youtube';
import type { RecipeDetail } from '@/types';

export default function RecipeDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<RecipeDetail | null>(null);
  const [fetchError, setFetchError] = useState(false);
  const [loading, setLoading] = useState(true);

  const ingredients = data?.ingredients ?? [];
  const { checked, toggle, allEssentialChecked, progressPct, checkedCount, reset } =
    useIngredientChecklist(ingredients);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setFetchError(false);
    reset();
    getRecipeBySlug(slug)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => { setFetchError(true); setLoading(false); });
  }, [slug]);

  const youtubeId = data?.sourceUrl ? getYouTubeId(data.sourceUrl) : null;

  const handleStartCooking = () => navigate(`/recipes/${slug}/cook`);
  const handleBack = () => navigate('/recipes');

  return (
    <div className="detail-page">

      {/* ── Sticky header ────────────────────── */}
      <header className="detail-header">
        <button className="detail-back-btn" onClick={handleBack} aria-label="Back to recipes">
          <BackIcon />
        </button>
        <span className="wordmark">Suvai</span>
        <span className="detail-header-title">{data?.title ?? slug}</span>
        <button className="detail-start-btn" onClick={handleStartCooking}>
          Start Cooking
        </button>
      </header>

      {/* ── Body ─────────────────────────────── */}
      {loading ? (
        <div className="detail-body">
          <div className="skeleton" style={{ height: 40, width: '60%', marginBottom: 10 }} />
          <div className="skeleton" style={{ height: 18, width: '22%', marginBottom: 40 }} />
          <div className="skeleton" style={{ width: '100%', aspectRatio: '16/9', borderRadius: 12, marginBottom: 52 }} />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 50, marginBottom: 10, borderRadius: 6 }} />
          ))}
        </div>
      ) : fetchError || !data ? (
        <div className="detail-body detail-error">
          <p>Could not load recipe.</p>
          <button onClick={handleBack} className="detail-error-back">← Back to list</button>
        </div>
      ) : (
        <div className="detail-body">

          {/* Title + cuisine */}
          <h1 className="detail-title">{data.title}</h1>
          {data.cuisine && (
            <div className="detail-cuisine-row">
              <span className="cuisine-tag">{data.cuisine}</span>
            </div>
          )}

          {/* ── YouTube ──────────────────────── */}
          {youtubeId ? (
            <div className="youtube-wrap">
              <iframe
                src={`https://www.youtube.com/embed/${youtubeId}`}
                title={data.title}
                allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              />
            </div>
          ) : (
            <div className="youtube-placeholder">Video not available</div>
          )}

          {/* ── Ingredients ──────────────────── */}
          {ingredients.length > 0 && (
            <section className="detail-section" aria-labelledby="ing-heading">
              <div className="section-head">
                <h2 className="section-title" id="ing-heading">Ingredients</h2>
                <span className="section-tally">
                  {allEssentialChecked
                    ? 'All ready'
                    : `${checkedCount} of ${ingredients.length}`}
                </span>
              </div>

              <div className="progress-track" role="progressbar" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
                <div className="progress-fill" style={{ transform: `scaleX(${progressPct / 100})` }} />
              </div>

              <ul className="ing-list" role="list">
                {ingredients.map((ing) => {
                  const isChecked = checked.has(ing.name);
                  return (
                    <li
                      key={ing.name}
                      className={`ing-row${isChecked ? ' ing-checked' : ''}`}
                      onClick={() => toggle(ing.name)}
                      role="checkbox"
                      aria-checked={isChecked}
                      tabIndex={0}
                      onKeyDown={(e) => e.key === ' ' && (e.preventDefault(), toggle(ing.name))}
                    >
                      <div className="ing-box" aria-hidden="true">
                        {isChecked && <CheckIcon />}
                      </div>
                      <div className="ing-info">
                        <span className="ing-name">{ing.name}</span>
                        {ing.notes && <span className="ing-note">{ing.notes}</span>}
                      </div>
                      <div className="ing-right">
                        {ing.quantity && <span className="ing-qty">{ing.quantity}</span>}
                        {ing.optional && <span className="ing-opt">optional</span>}
                      </div>
                    </li>
                  );
                })}
              </ul>

              {allEssentialChecked && (
                <p className="ing-ready" role="status">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  You have everything. Ready to cook.
                </p>
              )}
            </section>
          )}

          {/* ── Mise en Place ────────────────── */}
          {data.precookBriefing && (
            <section className="detail-section" aria-labelledby="mep-heading">
              <div className="section-head">
                <h2 className="section-title" id="mep-heading">Mise en Place</h2>
              </div>

              <blockquote className="briefing-quote">
                <p className="briefing-text">{data.precookBriefing.summary}</p>
              </blockquote>

              {data.precookBriefing.prepItems.length > 0 && (
                <ol className="prep-list" role="list">
                  {data.precookBriefing.prepItems.map((item, i) => (
                    <li key={`${item.task}-${i}`} className="prep-item">
                      <span className="prep-num" aria-hidden="true">
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <div className="prep-body">
                        <p className="prep-task">{item.task}</p>
                        <div className="prep-meta">
                          {item.duration && (
                            <span className="prep-dur">
                              <ClockIcon /> {item.duration}
                            </span>
                          )}
                          {item.ingredients.length > 0 && (
                            <div className="prep-ing-tags">
                              {item.ingredients.map((ing) => (
                                <span key={ing} className="prep-ing-tag">{ing}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        {item.notes && <p className="prep-note">{item.notes}</p>}
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          )}

          {/* ── Bottom CTA ───────────────────── */}
          <div className="detail-cta-block">
            <p className="detail-cta-caption">Ready to begin?</p>
            <button className="detail-cta-btn" onClick={handleStartCooking}>
              Begin Cooking Session
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>

        </div>
      )}
    </div>
  );
}

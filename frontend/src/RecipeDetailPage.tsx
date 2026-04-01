import { useState, useEffect } from "react";
import type { RecipeDetail } from "./types";

function getYouTubeId(url: string): string | null {
  const patterns = [/[?&]v=([^&\s]+)/, /youtu\.be\/([^?&\s]+)/, /embed\/([^?&\s]+)/];
  for (const p of patterns) {
    const m = url.match(p);
    if (m) return m[1];
  }
  return null;
}

function CheckIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l3.5 2" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M19 12H5M12 5l-7 7 7 7" />
    </svg>
  );
}

interface Props {
  recipeId: string;
  recipeTitle: string;
  onBack: () => void;
  onStartCooking: () => void;
  startLoading: boolean;
}

export default function RecipeDetailPage({
  recipeId,
  recipeTitle,
  onBack,
  onStartCooking,
  startLoading,
}: Props) {
  const [data, setData] = useState<RecipeDetail | null>(null);
  const [fetchError, setFetchError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [checked, setChecked] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    setFetchError(false);
    setChecked(new Set());
    fetch(`${import.meta.env.VITE_BACKEND_API_URL}/api/voice/recipes/${recipeId}`)
      .then((r) => {
        if (!r.ok) throw new Error("not found");
        return r.json();
      })
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => { setFetchError(true); setLoading(false); });
  }, [recipeId]);

  const toggle = (name: string) =>
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });

  const ingredients = data?.ingredients ?? [];
  const essentialCount = ingredients.filter((i) => !i.optional).length;
  const checkedCount = checked.size;
  const allEssentialChecked = essentialCount > 0 && ingredients.filter((i) => !i.optional && checked.has(i.name)).length === essentialCount;
  const progressPct = ingredients.length > 0 ? (checkedCount / ingredients.length) * 100 : 0;
  const youtubeId = data?.source_url ? getYouTubeId(data.source_url) : null;

  return (
    <div className="detail-page">

      {/* ── Sticky header ────────────────────── */}
      <header className="detail-header">
        <button className="detail-back-btn" onClick={onBack} aria-label="Back to recipes">
          <BackIcon />
        </button>
        <span className="wordmark">Suvai</span>
        <span className="detail-header-title">{recipeTitle}</span>
        <button
          className="detail-start-btn"
          onClick={onStartCooking}
          disabled={startLoading}
        >
          {startLoading ? "Starting…" : "Start Cooking"}
        </button>
      </header>

      {/* ── Body ─────────────────────────────── */}
      {loading ? (
        <div className="detail-body">
          <div className="skeleton" style={{ height: 40, width: "60%", marginBottom: 10 }} />
          <div className="skeleton" style={{ height: 18, width: "22%", marginBottom: 40 }} />
          <div className="skeleton" style={{ width: "100%", aspectRatio: "16/9", borderRadius: 12, marginBottom: 52 }} />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 50, marginBottom: 10, borderRadius: 6 }} />
          ))}
        </div>
      ) : fetchError || !data ? (
        <div className="detail-body detail-error">
          <p>Could not load recipe.</p>
          <button onClick={onBack} className="detail-error-back">← Back to list</button>
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
                    ? "All ready"
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
                      className={`ing-row${isChecked ? " ing-checked" : ""}`}
                      onClick={() => toggle(ing.name)}
                      role="checkbox"
                      aria-checked={isChecked}
                      tabIndex={0}
                      onKeyDown={(e) => e.key === " " && (e.preventDefault(), toggle(ing.name))}
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
          {data.precook_briefing && (
            <section className="detail-section" aria-labelledby="mep-heading">
              <div className="section-head">
                <h2 className="section-title" id="mep-heading">Mise en Place</h2>
              </div>

              {/* Summary quote */}
              <blockquote className="briefing-quote">
                <p className="briefing-text">{data.precook_briefing.summary}</p>
              </blockquote>

              {data.precook_briefing.prep_items.length > 0 && (
                <ol className="prep-list" role="list">
                  {data.precook_briefing.prep_items.map((item, i) => (
                    <li key={i} className="prep-item">
                      <span className="prep-num" aria-hidden="true">
                        {String(i + 1).padStart(2, "0")}
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
            <button
              className="detail-cta-btn"
              onClick={onStartCooking}
              disabled={startLoading}
            >
              {startLoading ? "Starting…" : "Begin Cooking Session"}
              {!startLoading && (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              )}
            </button>
          </div>

        </div>
      )}
    </div>
  );
}

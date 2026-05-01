import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@clerk/react';
import '@/styles/LandingPage.css';

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoaded && isSignedIn) navigate('/recipes', { replace: true });
  }, [isLoaded, isSignedIn, navigate]);

  return (
    <div className="landing-page">
      <header className="landing-header">
        <span className="wordmark">Suvai</span>
      </header>

      <main className="landing-main">
        <h1 className="landing-headline">
          Your hands-free<br />
          <em>kitchen companion</em>
        </h1>

        <p className="landing-body">
          Suvai follows your chosen recipe step by step - faithfully, by
          voice, so your hands never leave the kitchen. Missing an
          ingredient? Need to substitute something for an allergy? Dish
          too spicy or not tasting right? Just ask.
        </p>

        <div className="landing-features">
          <div className="landing-feature">
            <span className="landing-feature-mark">01</span>
            <div className="landing-feature-content">
              <span className="landing-feature-text">Faithful to the recipe</span>
              <span className="landing-feature-desc">
                Guides you through each step exactly as the creator intended
              </span>
            </div>
          </div>
          <div className="landing-feature">
            <span className="landing-feature-mark">02</span>
            <div className="landing-feature-content">
              <span className="landing-feature-text">Adapts when you need it</span>
              <span className="landing-feature-desc">
                Substitute ingredients, handle allergies, or work with what you have in your pantry
              </span>
            </div>
          </div>
          <div className="landing-feature">
            <span className="landing-feature-mark">03</span>
            <div className="landing-feature-content">
              <span className="landing-feature-text">Help when the taste is off</span>
              <span className="landing-feature-desc">
                Too salty, too bland, not quite right - get advice to course-correct mid-cook
              </span>
            </div>
          </div>
        </div>

        <Link to="/sign-in" className="landing-cta">
          Try the Demo
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </Link>

        <p className="landing-fine">
          3 curated recipes available - more being added from YouTube
        </p>
      </main>

      <footer className="landing-footer">
        <span>Suvai - powered by AI</span>
      </footer>
    </div>
  );
}

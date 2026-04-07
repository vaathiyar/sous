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
        <div className="landing-eyebrow">AI · Cooking · Voice</div>

        <h1 className="landing-headline">
          Your hands-free<br />
          <em>kitchen companion</em>
        </h1>

        <p className="landing-body">
          Pick a recipe. Let Suvai guide you through every step —
          entirely by voice, so your hands stay in the kitchen.
        </p>

        <div className="landing-features">
          <div className="landing-feature">
            <span className="landing-feature-mark">01</span>
            <span>Choose from curated recipes</span>
          </div>
          <div className="landing-feature">
            <span className="landing-feature-mark">02</span>
            <span>Start a voice cooking session</span>
          </div>
          <div className="landing-feature">
            <span className="landing-feature-mark">03</span>
            <span>Cook hands-free, ask anything</span>
          </div>
        </div>

        <Link to="/sign-in" className="landing-cta">
          Get Started
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </Link>

        <p className="landing-fine">Join the waitlist · 5 free cooking sessions</p>
      </main>

      <footer className="landing-footer">
        <span>Suvai — powered by AI</span>
      </footer>
    </div>
  );
}

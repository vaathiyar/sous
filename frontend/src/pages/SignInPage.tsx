import { SignIn } from '@clerk/react';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import '@/styles/SignInPage.css';

const clerkAppearance = {
  variables: {
    colorPrimary: '#bf3a1f',
    colorBackground: '#faf8f3',
    colorText: '#1c1a16',
    colorTextSecondary: '#5c5548',
    colorInputBackground: '#f3efe6',
    colorInputText: '#1c1a16',
    colorDanger: '#bf3a1f',
    borderRadius: '8px',
    fontFamily: "'Outfit', system-ui, sans-serif",
    fontFamilyButtons: "'Outfit', system-ui, sans-serif",
  },
  elements: {
    card: 'clerk-card',
    headerTitle: 'clerk-header-title',
    headerSubtitle: 'clerk-header-subtitle',
    socialButtonsBlockButton: 'clerk-social-btn',
    formButtonPrimary: 'clerk-btn-primary',
    footerActionLink: 'clerk-footer-link',
    dividerLine: 'clerk-divider-line',
    dividerText: 'clerk-divider-text',
  },
};

export default function SignInPage() {
  const [params] = useSearchParams();
  const redirectUrl = params.get('redirect_url') ?? '/recipes';

  return (
    <div className="signin-page">
      <Link to="/" className="signin-wordmark wordmark">Suvai</Link>

      <div className="signin-form-wrap">
        <SignIn
          routing="path"
          path="/sign-in"
          fallbackRedirectUrl="/recipes"
          forceRedirectUrl={redirectUrl}
          appearance={clerkAppearance}
        />
      </div>
    </div>
  );
}

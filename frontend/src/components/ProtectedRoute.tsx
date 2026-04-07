import { useAuth } from '@clerk/react';
import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isSignedIn, isLoaded } = useAuth();
  const location = useLocation();

  // Wait for Clerk to hydrate before deciding — avoids flash redirect
  if (!isLoaded) return null;

  if (!isSignedIn) {
    const redirectUrl = encodeURIComponent(location.pathname);
    return <Navigate to={`/sign-in?redirect_url=${redirectUrl}`} replace />;
  }

  return <>{children}</>;
}

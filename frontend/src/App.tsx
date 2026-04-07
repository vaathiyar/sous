import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from '@/pages/LandingPage';
import SignInPage from '@/pages/SignInPage';
import RecipeListPage from '@/pages/RecipeListPage';
import RecipeDetailPage from '@/pages/RecipeDetailPage';
import CookPage from '@/pages/CookPage';
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/sign-in/*" element={<SignInPage />} />
        <Route
          path="/recipes"
          element={
            <ProtectedRoute>
              <RecipeListPage />
            </ProtectedRoute>
          }
        />
        <Route path="/recipes/:slug" element={<RecipeDetailPage />} />
        <Route
          path="/recipes/:slug/cook"
          element={
            <ProtectedRoute>
              <CookPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

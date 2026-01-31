import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { AppLayout } from '@/components/layout/AppLayout';

// Pages
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { ConsentPage } from '@/pages/ConsentPage';
import { AgeVerifyPage } from '@/pages/AgeVerifyPage';
import { MarketplacePage } from '@/pages/MarketplacePage';
import { PackDetailPage } from '@/pages/PackDetailPage';
import { ConversationPage } from '@/pages/ConversationPage';
import { ConversationsPage } from '@/pages/ConversationsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { PartnerCreatePage } from '@/pages/PartnerCreatePage';

// Loading component
function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center">
        <span className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          AI will
        </span>
        <div className="mt-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
        </div>
      </div>
    </div>
  );
}

// Route guard for authenticated users
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, onboarding } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check onboarding status
  if (onboarding && !onboarding.consent_completed) {
    return <Navigate to="/onboarding/consent" replace />;
  }

  if (onboarding && !onboarding.age_verified) {
    return <Navigate to="/onboarding/age" replace />;
  }

  return <>{children}</>;
}

// Route guard for onboarding pages
function RequireAuthOnly({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Route guard for public pages (redirect if authenticated)
function PublicOnly({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, onboarding } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    // Redirect based on onboarding status
    if (onboarding && !onboarding.consent_completed) {
      return <Navigate to="/onboarding/consent" replace />;
    }
    if (onboarding && !onboarding.age_verified) {
      return <Navigate to="/onboarding/age" replace />;
    }
    return <Navigate to="/marketplace" replace />;
  }

  return <>{children}</>;
}

// Initial redirect component
function InitialRedirect() {
  const { isAuthenticated, isLoading, onboarding } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (onboarding && !onboarding.consent_completed) {
    return <Navigate to="/onboarding/consent" replace />;
  }

  if (onboarding && !onboarding.age_verified) {
    return <Navigate to="/onboarding/age" replace />;
  }

  return <Navigate to="/marketplace" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Initial redirect */}
      <Route path="/" element={<InitialRedirect />} />

      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicOnly>
            <LoginPage />
          </PublicOnly>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnly>
            <RegisterPage />
          </PublicOnly>
        }
      />

      {/* Onboarding routes */}
      <Route
        path="/onboarding/consent"
        element={
          <RequireAuthOnly>
            <ConsentPage />
          </RequireAuthOnly>
        }
      />
      <Route
        path="/onboarding/age"
        element={
          <RequireAuthOnly>
            <AgeVerifyPage />
          </RequireAuthOnly>
        }
      />

      {/* Protected routes with layout */}
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/marketplace" element={<MarketplacePage />} />
        <Route path="/marketplace/:packId" element={<PackDetailPage />} />
        <Route path="/conversations" element={<ConversationsPage />} />
        <Route path="/conversation/:threadId" element={<ConversationPage />} />
        <Route path="/partner-create" element={<PartnerCreatePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

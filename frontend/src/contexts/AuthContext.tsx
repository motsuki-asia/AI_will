import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import * as api from '@/lib/api';

interface User {
  id: string;
  email: string;
  display_name: string | null;
  consent_at: string | null;
  age_verified_at: string | null;
  age_group: string | null;
}

interface Onboarding {
  consent_completed: boolean;
  age_verified: boolean;
  completed: boolean;
}

interface AuthContextType {
  user: User | null;
  onboarding: Onboarding | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  consent: () => Promise<void>;
  ageVerify: (ageGroup: 'u13' | 'u18' | 'adult') => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [onboarding, setOnboarding] = useState<Onboarding | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const data = await api.getMe();
      setUser(data.user);
      setOnboarding(data.onboarding);
    } catch {
      setUser(null);
      setOnboarding(null);
    }
  };

  useEffect(() => {
    const init = async () => {
      if (api.getAccessToken()) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    init();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    setUser(data.user);
    setOnboarding(data.onboarding);
  };

  const register = async (email: string, password: string) => {
    const data = await api.register(email, password);
    setUser(data.user);
    setOnboarding(data.onboarding);
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    setOnboarding(null);
  };

  const consent = async () => {
    const data = await api.consent('1.0', '1.0');
    setUser(data.user);
    setOnboarding(data.onboarding);
  };

  const ageVerify = async (ageGroup: 'u13' | 'u18' | 'adult') => {
    const data = await api.ageVerify(ageGroup);
    setUser(data.user);
    setOnboarding(data.onboarding);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        onboarding,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        consent,
        ageVerify,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

"use client";

/**
 * Auth context for FINRLX beta (Phase MVP-4).
 *
 * Tokens stored in localStorage. Acceptable for a closed 5-15 peer beta;
 * promotes to HTTP-only cookies in MVP-5 (security hardening).
 *
 * Public API:
 *   - useAuth() — returns { user, isLoading, login, signup, logout }
 *   - getAccessToken() — used by apiFetch to inject Bearer header
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

import {
  AuthUser,
  signup as apiSignup,
  login as apiLogin,
  logout as apiLogout,
  refreshTokens as apiRefresh,
  getMe,
  setAccessToken,
  getAccessToken,
  setRefreshToken,
  getRefreshToken,
  clearTokens,
} from "@/services/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  login: async () => {},
  signup: async () => {},
  logout: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: try /auth/me with stored access token. If 401 and we have a
  // refresh token, attempt rotation. Otherwise: no user, no error.
  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      const access = getAccessToken();
      if (!access) {
        if (mounted) setIsLoading(false);
        return;
      }
      try {
        const me = await getMe();
        if (mounted) setUser(me);
      } catch {
        const refresh = getRefreshToken();
        if (!refresh) {
          clearTokens();
          if (mounted) setIsLoading(false);
          return;
        }
        try {
          const pair = await apiRefresh(refresh);
          setAccessToken(pair.access_token);
          setRefreshToken(pair.refresh_token);
          const me = await getMe();
          if (mounted) setUser(me);
        } catch {
          clearTokens();
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    setAccessToken(res.tokens.access_token);
    setRefreshToken(res.tokens.refresh_token);
    setUser(res.user);
  }, []);

  const signup = useCallback(async (email: string, password: string) => {
    const res = await apiSignup(email, password);
    setAccessToken(res.tokens.access_token);
    setRefreshToken(res.tokens.refresh_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(async () => {
    const refresh = getRefreshToken();
    if (refresh) {
      try {
        await apiLogout(refresh);
      } catch {
        // Best-effort. Backend may already have revoked.
      }
    }
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

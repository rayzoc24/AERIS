/**
 * Auth context provider.
 *
 * Holds the currently authenticated user (if any). The user object is
 * cached in-memory only. The actual JWT tokens stay in HttpOnly cookies
 * managed by the browser, so they cannot be exfiltrated by JS.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as api from "@/api";
import type { UserRole, UserOut } from "@/api/types";

interface AuthState {
  user: UserOut | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasRole: (...roles: UserRole[]) => boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: api.RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await api.getMe();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const bundle = await api.login({ email, password });
    setUser(bundle.user);
  }, []);

  const register = useCallback(async (payload: api.RegisterPayload) => {
    const bundle = await api.register(payload);
    setUser(bundle.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } catch {
      // Ignore; cookies are cleared server-side regardless.
    } finally {
      setUser(null);
    }
  }, []);

  const hasRole = useCallback((...roles: UserRole[]) => {
    if (!user) return false;
    return roles.includes(user.role);
  }, [user]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      hasRole,
      login,
      register,
      logout,
    }),
    [user, isLoading, hasRole, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

"use client";
import { createContext, useContext, useMemo, useState, useEffect } from "react";

type AuthCtx = { token: string | null; setToken: (t: string | null) => void };
const Ctx = createContext<AuthCtx>({ token: null, setToken: () => {} });
export const useAuth = () => useContext(Ctx);

const TOKEN_KEY = "auth_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, _setToken] = useState<string | null>(null);

  // Helper that persists to sessionStorage
  const setToken = (t: string | null) => {
    _setToken(t);
    if (typeof window !== "undefined") {
      if (t) sessionStorage.setItem(TOKEN_KEY, t);
      else sessionStorage.removeItem(TOKEN_KEY);
    }
  };

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleTokenUpdate = () => {
      // 1) Try to read from URL fragment
      const hash = window.location.hash || "";
      const params = new URLSearchParams(hash.startsWith("#") ? hash.slice(1) : hash);
      const fragmentToken = params.get("access_token") || params.get("id_token");
      
      if (fragmentToken) {
        setToken(fragmentToken);
        // Remove token from the address bar to avoid leaks
        window.history.replaceState(null, "", window.location.pathname);
        return;
      }

      // 2) Fallback to sessionStorage if present (persist across same-tab reloads)
      const stored = sessionStorage.getItem(TOKEN_KEY);
      if (stored && stored !== token) {
        _setToken(stored);
      }
    };

    // Initial check
    handleTokenUpdate();

    // Listen for hash changes (for OAuth redirects)
    window.addEventListener('hashchange', handleTokenUpdate);
    
    // Cleanup
    return () => {
      window.removeEventListener('hashchange', handleTokenUpdate);
    };
  }, [token]);

  const value = useMemo(() => ({ token, setToken }), [token]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}


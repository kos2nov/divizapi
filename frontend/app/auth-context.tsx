"use client";
import { createContext, useContext, useMemo, useState, useEffect, useCallback } from "react";

type AuthCtx = { 
  token: string | null; 
  setToken: (t: string | null) => void;
  logout: () => void;
};

const Ctx = createContext<AuthCtx>({ 
  token: null, 
  setToken: () => {},
  logout: () => {}
});

export const useAuth = () => useContext(Ctx);

const TOKEN_KEY = "id_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, _setToken] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Helper that persists to sessionStorage
  const setToken = useCallback((t: string | null) => {
    _setToken(t);
    if (typeof window !== "undefined") {
      if (t) {
        sessionStorage.setItem(TOKEN_KEY, t);
      } else {
        sessionStorage.removeItem(TOKEN_KEY);
      }
    }
  }, []);

  const logout = useCallback(() => {
    _setToken(null);
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      // Clear URL hash
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (e) {
      console.error('Failed to remove auth token', e);
    }
  }, []);

  // Handle token from URL hash on initial load
  useEffect(() => {
    if (typeof window === "undefined" || isInitialized) return;

    // Check if we're coming back from OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    
    if (code) {
      // We have an authorization code, exchange it for tokens
      const exchangeCodeForToken = async () => {
        try {
          const response = await fetch(`/auth/callback?code=${code}`);
          if (!response.ok) {
            throw new Error('Failed to exchange code for token');
          }
          
          const data = await response.json();
          if (data.id_token) {
            setToken(data.id_token);
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        } catch (error) {
          console.error('Error exchanging code for token:', error);
        } finally {
          setIsInitialized(true);
        }
      };
      
      exchangeCodeForToken();
      return;
    }

    // Check for token in URL hash (fallback)
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const tokenFromHash = params.get('id_token');
      
      if (tokenFromHash) {
        setToken(tokenFromHash);
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        setIsInitialized(true);
        return;
      }
    }

    // If no token in URL, try to get from session storage
    try {
      const storedToken = sessionStorage.getItem(TOKEN_KEY);
      if (storedToken) {
        setToken(storedToken);
      }
    } catch (e) {
      console.error('Failed to read auth token', e);
    }
    
    setIsInitialized(true);
  }, [setToken, isInitialized]);

  const value = useMemo(() => ({
    token,
    setToken,
    logout
  }), [token, setToken, logout]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}


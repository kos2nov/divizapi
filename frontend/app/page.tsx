"use client";
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './auth-context';
import console from 'console';

type UserResp = { current_user?: Record<string, any>; detail?: string };

function MeetForm() {
  const { token } = useAuth();
  const [code, setCode] = useState('');
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErr('Please log in first');
      return;
    }

    setLoading(true);
    setErr(null);
    setResult(null);
    
    try {
      const res = await fetch(`/api/meet/${encodeURIComponent(code)}`, {
        method: 'GET',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (res.status === 401) {
        // Token might be expired, clear it and redirect to login
        router.push('/login');
        return;
      }

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || 'Request failed');
      }

      const json = await res.json();
      setResult(json);
    } catch (e: any) {
      setErr(e?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  

  return (
    <>
      <form onSubmit={onSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter Google Meet code"
          style={{ flex: 1, padding: '8px 10px', borderRadius: 8, border: '1px solid #334155', background: '#0b1220', color: '#e2e8f0' }}
        />
        <button type="submit" disabled={loading || !code} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #1e293b', background: '#1d4ed8', color: '#fff' }}>
          {loading ? 'Loading...' : 'Check'}
        </button>
      </form>
      <div style={{ marginTop: 12 }}>
        {err && <p style={{ color: '#fca5a5' }}>{err}</p>}
        {result && (
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </>
  )
}


function TokenPanel() {
  const { token } = useAuth()
  const [showToken, setShowToken] = useState(false)
  const [decodedToken, setDecodedToken] = useState<any>(null)

  useEffect(() => {
    if (token) {
      try {
        const base64Url = token.split('.')[1]
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        )
        setDecodedToken(JSON.parse(jsonPayload))
      } catch (e) {
        console.error('Error decoding token:', e)
        setDecodedToken(null)
      }
    } else {
      setDecodedToken(null)
    }
  }, [token])

  return (
    <div>
      <div 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: token ? 'pointer' : 'default', marginBottom: showToken ? 12 : 0 }}
        onClick={() => token && setShowToken(!showToken)}
      >
        <h2 style={{ fontSize: 20, margin: 0 }}>Authentication Token</h2>
        <span>{token ? (showToken ? '▲' : '▼') : '🔒'}</span>
      </div>

      {token ? (
        showToken && (
          <div>
            <div style={{ marginBottom: 12 }}>
              <h4 style={{ margin: '8px 0' }}>Encoded</h4>
              <div style={{ background: '#0b1220', border: '1px solid #334155', padding: '10px', borderRadius: 8, overflowWrap: 'break-word', fontSize: '0.9em' }}>
                {token}
              </div>
            </div>
            <div>
              <h4 style={{ margin: '8px 0' }}>Decoded</h4>
              <pre style={{ background: '#0b1220', border: '1px solid #334155', padding: '10px', borderRadius: 8, maxHeight: 300, overflow: 'auto', fontSize: '0.85em', margin: 0 }}>
                {JSON.stringify(decodedToken, null, 2)}
              </pre>
            </div>
          </div>
        )
      ) : (
        <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>
          No authentication token available. Please sign in to see token details.
        </div>
      )}
    </div>
  )
}


export default function Page() {
  const { token, logout } = useAuth();
  const [data, setData] = useState<UserResp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    if (!token) {
      setData(null);
      setError('Not authenticated');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('/api/user', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (res.status === 401) {
        // Token might be expired, clear it and redirect to login
        logout();
        router.push('/login');
        return;
      }
      
      if (!res.ok) {
        throw new Error('Failed to fetch user data');
      }
      
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error('Error fetching user:', err);
      setError('Failed to load user data');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [token, router, logout]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return (
    <main style={{ maxWidth: 960, margin: '40px auto', padding: '0 20px' }}>
      <header style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, margin: 0 }}>DiViz</h1>
          <p style={{ color: '#94a3b8', marginTop: 8 }}>Meeting Efficiency Demo Application</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
        <a
            href="https://auth.diviz.knovoselov.com/oauth2/authorize?identity_provider=Google&client_id=5tb6pekknkes6eair7o39b3hh7&response_type=code&redirect_uri=https://diviz.knovoselov.com/auth/callback&scope=email%20openid%20profile"
            style={{ background: '#1d4ed8', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #1e293b' }}
          >
            Login
          </a>
          {!token ? (
            <a
              href="https://auth.diviz.knovoselov.com/login?client_id=5tb6pekknkes6eair7o39b3hh7&response_type=code&scope=email+openid+profile&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fauth%2Fcallback"
              style={{ background: '#1d4ed8', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #1e293b' }}
            >
              Cognito
            </a>
          ) : (
            <>
              <button
                onClick={async () => {
                  try {
                    console.log("Google connect token: ", token);
                    const response = await fetch('/api/google/connect', {
                      headers: { 
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                      },
                    });
                    
                    console.log("Google connect response: ", response);
                    if (response.ok) {
                      const data = await response.json();
                      console.log("Redirecting to Google OAuth: ", data.authorization_url);
                      window.location.href = data.authorization_url;
                    } else {
                      throw new Error('Failed to connect Google');
                    }
                  } catch (error) {
                    console.error('Error connecting Google:', error);
                    // Handle error as needed
                  }
                }}
                style={{ 
                  background: '#4285F4', 
                  color: '#fff', 
                  padding: '8px 12px', 
                  borderRadius: 8, 
                  textDecoration: 'none', 
                  border: '1px solid #1e293b', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 8,
                  cursor: 'pointer'
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                Google
              </button>
              <button
                onClick={() => {
                  logout();
                  window.location.href = 'https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fstatic%2Findex.html';
                }}
                style={{ background: 'transparent', color: '#e2e8f0', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #334155' }}
              >
                Logout
              </button>
            </>
          )}
        </div>
      </header>

      <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 20, margin: 0 }}>User</h2>
          <button 
            onClick={fetchUser}
            disabled={loading}
            style={{
              background: 'transparent',
              border: '1px solid #334155',
              color: '#e2e8f0',
              borderRadius: 6,
              padding: '4px 8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              opacity: loading ? 0.7 : 1,
              pointerEvents: loading ? 'none' : 'auto'
            }}
            title="Refresh user data"
          >
            <svg 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              style={{
                animation: loading ? 'spin 1s linear infinite' : 'none',
                transformOrigin: 'center'
              }}
            >
              <path d="M21.5 2v6h-6M2.5 22v-6h6M22 12.5a10 10 0 0 0-17-7.5M2 12.5a10 10 0 0 0 17 7.5"/>
            </svg>
            Refresh
          </button>
        </div>
        {!data && !error && <p>Loading...</p>}
        {error && <p style={{ color: '#fca5a5' }}>{error}</p>}
        {data && (
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
        <style jsx global>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </section>
      <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16, marginTop: 16 }}>
        <h2 style={{ fontSize: 20, marginTop: 0, marginBottom: 12 }}>Meet</h2>
        <MeetForm />
      </section>
      <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16, marginTop: 16 }}>
        <TokenPanel />
      </section>
    </main>
  )
}



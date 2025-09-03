"use client";
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './auth-context';

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
            Google
          </a>
          {!token ? (
            <a
              href="https://auth.diviz.knovoselov.com/login?client_id=5tb6pekknkes6eair7o39b3hh7&response_type=code&scope=email+openid+profile&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fauth%2Fcallback"
              style={{ background: '#1d4ed8', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #1e293b' }}
            >
              Login
            </a>
          ) : (
            <button
              onClick={() => {
                logout();
                window.location.href = 'https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fstatic%2Findex.html';
              }}
              style={{ background: 'transparent', color: '#e2e8f0', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #334155' }}
            >
              Logout
            </button>
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



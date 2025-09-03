"use client";
import { useEffect, useState } from 'react'

import { useAuth } from './auth-context'

type UserResp = { current_user?: Record<string, any>; detail?: string }
function MeetForm() {
  const { token } = useAuth()
  const [code, setCode] = useState('')
  const [result, setResult] = useState<any>(null)
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setErr(null)
    setResult(null)
    try {
      const res = await fetch(`/api/meet/${encodeURIComponent(code)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      const json = await res.json()
      setResult(json)
    } catch (e: any) {
      setErr(e?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  

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
  const { token } = useAuth();
  const [data, setData] = useState<UserResp | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await fetch('/api/user', {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        })
        const json = await res.json()
        setData(json)
      } catch (e: any) {
        setError(e?.message || 'Error fetching user')
      }
    }
    fetchUser()
  }, [])

  return (
    <main style={{ maxWidth: 960, margin: '40px auto', padding: '0 20px' }}>
      <header style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, margin: 0 }}>DiViz</h1>
          <p style={{ color: '#94a3b8', marginTop: 8 }}>Meeting Efficiency Demo Application</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <a
            href="https://auth.diviz.knovoselov.com/login?client_id=5tb6pekknkes6eair7o39b3hh7&response_type=code&scope=email+openid+profile&redirect_uri=https%3A%2F%2Fdiviz.knovoselov.com%2Fauth%2Fcallback"
            style={{ background: '#1d4ed8', color: '#fff', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #1e293b' }}
          >
            Login
          </a>
          <button
            onClick={() => {
              // Clear in-memory/session token and redirect to Cognito logout
              try { window.sessionStorage.removeItem('auth_token'); } catch {}
              window.location.href = 'https://auth.diviz.knovoselov.com/logout?client_id=5tb6pekknkes6eair7o39b3hh7&logout_uri=https%3A%2F%2Fdiviz.knovoselov.com';
            }}
            style={{ background: 'transparent', color: '#e2e8f0', padding: '8px 12px', borderRadius: 8, textDecoration: 'none', border: '1px solid #334155' }}
          >
            Logout
          </button>
        </div>
      </header>

      <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16 }}>
        <h2 style={{ fontSize: 20, marginTop: 0, marginBottom: 12 }}>User</h2>
        {!data && !error && <p>Loading...</p>}
        {error && <p style={{ color: '#fca5a5' }}>{error}</p>}
        {data && (
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        )}

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



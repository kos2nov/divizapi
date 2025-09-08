"use client";
import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from './auth-context';
import Script from 'next/script';

// Public env vars must be provided in the frontend runtime
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID as string | undefined;
const GOOGLE_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_API_KEY as string | undefined;

type UserResp = { current_user?: Record<string, any>; detail?: string };

type MeetFormProps = {
  onSearch: (code: string) => Promise<any>;
  missingGoogleEnv: boolean;
};

function MeetForm({ onSearch, missingGoogleEnv }: MeetFormProps) {
  const [code, setCode] = useState('');
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState<any>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);
  const [transcriptError, setTranscriptError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const { token } = useAuth();

  const fetchTranscript = async (meetCode: string) => {
    if (!token) {
      setTranscriptError('Authentication required for transcript');
      return;
    }
    
    setTranscriptLoading(true);
    setTranscriptError(null);
    
    try {
      const response = await fetch(`/api/fireflies/${meetCode}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.status === 404) {
        setTranscriptError('No transcript found for this meeting');
        return;
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch transcript');
      }
      
      const transcriptData = await response.json();
      setTranscript(transcriptData);
    } catch (error: any) {
      setTranscriptError(error.message || 'Failed to load transcript');
    } finally {
      setTranscriptLoading(false);
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    setResult(null);
    setTranscript(null);
    setTranscriptError(null);
    setAnalysis(null);
    setAnalysisError(null);
    
    try {
      if (missingGoogleEnv) {
        throw new Error('Missing Google Client ID or API Key. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID and NEXT_PUBLIC_GOOGLE_API_KEY.');
      }
      const json = await onSearch(code);
      if (!json) throw new Error('No results');
      setResult(json);
      
      // Extract meet code from the result and fetch transcript
      const firstMatch = json?.matches && json.matches.length > 0 ? json.matches[0] : null;
      const ev = firstMatch?.event;
      if (ev) {
        const meetUrl = ev?.hangoutLink || (ev?.conferenceData?.entryPoints || []).find((ep: any) => ep.uri)?.uri;
        if (meetUrl) {
          const meetCodeMatch = meetUrl.match(/meet\.google\.com\/(?:lookup\/)?([a-z\-]+)/i);
          if (meetCodeMatch) {
            await fetchTranscript(meetCodeMatch[1]);
          }
        }
      }
    } catch (e: any) {
      setErr(e?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  // Whether we have Meet details in the currently loaded result
  const hasMeetDetails = (() => {
    const firstMatch = result?.matches && result.matches.length > 0 ? result.matches[0] : null;
    const ev = firstMatch?.event;
    if (!ev) return false;
    const meetUrl = ev?.hangoutLink || (ev?.conferenceData?.entryPoints || []).find((ep: any) => ep.uri)?.uri;
    return !!meetUrl;
  })();

  const onAnalyze = async () => {
    if (analysisLoading) return;
    if (!token) {
      setAnalysisError('Authentication required for analysis');
      return;
    }
    const firstMatch = result?.matches && result.matches.length > 0 ? result.matches[0] : null;
    const ev = firstMatch?.event;
    if (!ev) {
      setAnalysisError('No meeting selected to analyze');
      return;
    }

    const meetUrl = ev?.hangoutLink || (ev?.conferenceData?.entryPoints || []).find((ep: any) => ep.uri)?.uri;
    const meetCodeMatch = meetUrl ? meetUrl.match(/meet\.google\.com\/(?:lookup\/)?([a-z\-]+)/i) : null;
    const meet_code = (meetCodeMatch && meetCodeMatch[1]) || result?.normalizedCode || '';
    const startISO = ev?.start?.dateTime || ev?.start?.date || '';
    const endISO = ev?.end?.dateTime || ev?.end?.date || '';

    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysis(null);
    try {
      const resp = await fetch('/api/analyze/meet/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meet_code,
          title: ev?.summary || 'No title',
          start_time: startISO,
          end_time: endISO,
        }),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || 'Failed to analyze meeting');
      }
      const data = await resp.json();
      setAnalysis(data);
    } catch (error: any) {
      setAnalysisError(error?.message || 'Failed to analyze meeting');
    } finally {
      setAnalysisLoading(false);
    }
  };

  

  return (
    <>
      <form onSubmit={onSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter Google Meet code"
          style={{ flex: 1, padding: '8px 10px', borderRadius: 8, border: '1px solid #334155', background: '#0b1220', color: '#e2e8f0' }}
        />
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" disabled={loading || !code} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #1e293b', background: '#1d4ed8', color: '#fff' }}>
            {loading ? 'Loading...' : 'Check'}
          </button>
          {hasMeetDetails && (
            <button
              type="button"
              onClick={onAnalyze}
              disabled={analysisLoading}
              style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #1e293b', background: '#059669', color: '#fff', opacity: analysisLoading ? 0.7 : 1, cursor: analysisLoading ? 'not-allowed' : 'pointer' }}
              title="Analyze this meeting"
            >
              {analysisLoading ? 'Analyzing...' : 'Analyze'}
            </button>
          )}
        </div>
      </form>
      <div style={{ marginTop: 12 }}>
        {err && <p style={{ color: '#fca5a5' }}>{err}</p>}
        {result && (
          (() => {
            const firstMatch = result?.matches && result.matches.length > 0 ? result.matches[0] : null;
            const ev = firstMatch?.event;
            console.log('Found Event', ev);
            if (!ev) {
              return (
                <div style={{ color: '#94a3b8' }}>No matching events found for code "{result?.normalizedCode ?? ''}".</div>
              );
            }

            const startISO = ev?.start?.dateTime || ev?.start?.date || null;
            const endISO = ev?.end?.dateTime || ev?.end?.date || null;
            const startDate = startISO ? new Date(startISO) : null;
            const endDate = endISO ? new Date(endISO) : null;
            const startStr = startDate ? startDate.toLocaleString() : 'N/A';
            const durationMs = startDate && endDate ? (endDate.getTime() - startDate.getTime()) : null;
            const durationStr = (() => {
              if (durationMs == null || isNaN(durationMs)) return 'N/A';
              const mins = Math.max(0, Math.round(durationMs / 60000));
              const h = Math.floor(mins / 60);
              const m = mins % 60;
              return h > 0 ? `${h}h ${m}m` : `${m}m`;
            })();

            const organizerEmail = ev?.organizer?.email || 'N/A';
            const ep = (ev?.conferenceData?.entryPoints || []) as Array<any>;
            const firstEpUrl = ep.length > 0 ? (ep[0]?.uri || '') : '';
            const meetUrl = firstEpUrl || ev?.hangoutLink || '';

            return (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 12 }}>
                <div style={{ border: '1px solid #334155', borderRadius: 8, padding: 12, background: '#0b1220' }}>
                  <h3 style={{ marginTop: 0, marginBottom: 10, fontSize: 18 }}>Meeting Info</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'max-content 1fr', rowGap: 6, columnGap: 10 }}>
                    <div style={{ color: '#94a3b8' }}>ID</div>
                    <div style={{ wordBreak: 'break-word' }}>{ev?.id || 'N/A'}</div>

                    <div style={{ color: '#94a3b8' }}>Summary</div>
                    <div>{ev?.summary || 'N/A'}</div>

                    <div style={{ color: '#94a3b8' }}>Start</div>
                    <div>{startStr}</div>

                    <div style={{ color: '#94a3b8' }}>Duration</div>
                    <div>{durationStr}</div>

                    <div style={{ color: '#94a3b8' }}>Organizer</div>
                    <div>{organizerEmail}</div>

                    <div style={{ color: '#94a3b8' }}>URL</div>
                    <div>
                      {meetUrl ? (
                        <a href={meetUrl} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>{meetUrl}</a>
                      ) : (
                        'N/A'
                      )}
                    </div>

                    <div style={{ color: '#94a3b8' }}>Description</div>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{ev?.description || '—'}</div>
                  </div>
                </div>

                <div style={{ border: '1px solid #334155', borderRadius: 8, padding: 12, background: '#0b1220' }}>
                  <h3 style={{ marginTop: 0, marginBottom: 10, fontSize: 18 }}>Transcript</h3>
                  {transcriptLoading && <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>Loading transcript...</div>}
                  {transcriptError && <div style={{ color: '#fca5a5' }}>{transcriptError}</div>}
                  {transcript && (
                    <div style={{ maxHeight: 400, overflow: 'auto' }}>
                      {transcript.transcript_id && (
                        <div style={{ marginBottom: 8 }}>
                          <strong style={{ color: '#94a3b8' }}>Transcript:</strong>{' '}
                          <a
                            href={`https://app.fireflies.ai/view/${transcript.transcript_id}?channelSource=all`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: '#60a5fa' }}
                          >
                            {transcript.transcript_id}
                          </a>
                        </div>
                      )}
                      {transcript.sentences && transcript.sentences.length > 0 ? (
                        <div style={{ lineHeight: 1.6 }}>
                          {transcript.sentences.map((sentence: any, index: number) => (
                            <div key={index} style={{ marginBottom: 8 }}>
                              <span style={{ color: '#60a5fa', fontWeight: 'bold' }}>
                                {sentence.speaker_name || 'Unknown'}:
                              </span>
                              <span style={{ marginLeft: 8 }}>
                                {sentence.text || sentence.raw_text}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>No transcript sentences available.</div>
                      )}
                      {transcript.summary && (
                        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #334155' }}>
                          <h4 style={{ marginTop: 0, marginBottom: 8, color: '#e2e8f0' }}>Summary</h4>
                          {transcript.summary.overview && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Overview:</strong> {transcript.summary.overview}
                            </div>
                          )}
                          {transcript.summary.short_summary && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Short Summary:</strong> {transcript.summary.short_summary}
                            </div>
                          )}
                          {transcript.summary.bullet_gist && Array.isArray(transcript.summary.bullet_gist) && transcript.summary.bullet_gist.length > 0 && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Key Points:</strong>
                              <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                                {transcript.summary.bullet_gist.map((point: string, index: number) => (
                                  <li key={index} style={{ color: '#e2e8f0' }}>{point}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {transcript.summary.bullet_gist && !Array.isArray(transcript.summary.bullet_gist) && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Key Points:</strong>
                              <div style={{ marginTop: 4, color: '#e2e8f0' }}>{transcript.summary.bullet_gist}</div>
                            </div>
                          )}
                          {transcript.summary.action_items && Array.isArray(transcript.summary.action_items) && transcript.summary.action_items.length > 0 && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Action Items:</strong>
                              <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                                {transcript.summary.action_items.map((item: string, index: number) => (
                                  <li key={index} style={{ color: '#e2e8f0' }}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {transcript.summary.action_items && !Array.isArray(transcript.summary.action_items) && (
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Action Items:</strong>
                              <div style={{ marginTop: 4, color: '#e2e8f0' }}>{transcript.summary.action_items}</div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  {!transcript && !transcriptLoading && !transcriptError && (
                    <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>No transcript available yet.</div>
                  )}
                </div>
                {(analysisLoading || analysisError || analysis) && (
                  <div style={{ border: '1px solid #334155', borderRadius: 8, padding: 12, background: '#0b1220' }}>
                    <h3 style={{ marginTop: 0, marginBottom: 10, fontSize: 18 }}>Analysis</h3>
                    {analysisLoading && (
                      <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>Analyzing meeting...</div>
                    )}
                    {analysisError && (
                      <div style={{ color: '#fca5a5' }}>{analysisError}</div>
                    )}
                    {analysis && (
                      <div>
                        {analysis.transcript_id && (
                          <div style={{ marginBottom: 8 }}>
                            <strong style={{ color: '#94a3b8' }}>Transcript ID:</strong>{' '}
                            <span style={{ color: '#e2e8f0' }}>{analysis.transcript_id}</span>
                          </div>
                        )}
                        {analysis.stats && (
                          <div>
                            <div style={{ marginBottom: 8 }}>
                              <strong style={{ color: '#94a3b8' }}>Speaking Duration:</strong>{' '}
                              <span style={{ color: '#e2e8f0' }}>{analysis.stats.total_duration_minutes} min</span>
                            </div>
                            {analysis.stats.speaker_minutes && (
                              <div>
                                <strong style={{ color: '#94a3b8' }}>Speaker Time:</strong>
                                <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                                  {Object.entries(analysis.stats.speaker_minutes).map(([speaker, minutes]: [string, any]) => (
                                    <li key={speaker} style={{ color: '#e2e8f0' }}>
                                      {speaker}: {typeof minutes === 'number' ? minutes.toFixed(2) : minutes} min
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })()
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
  const [activeTab, setActiveTab] = useState<'user' | 'meet'>('user');

  // Google auth/client state (client-side only)
  const [gapiLoaded, setGapiLoaded] = useState(false);
  const [gapiInited, setGapiInited] = useState(false);
  const [gisLoaded, setGisLoaded] = useState(false);
  const [googleAccessToken, setGoogleAccessToken] = useState<string | null>(null);
  const tokenClientRef = useRef<any>(null);

  // Persisted token storage keys
  const GOOGLE_TOKEN_KEY = 'google_access_token';
  const GOOGLE_TOKEN_EXPIRES_AT_KEY = 'google_access_token_expires_at';

  const missingGoogleEnv = !GOOGLE_CLIENT_ID || !GOOGLE_API_KEY;

  // Initialize gapi client after script load
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!gapiLoaded || gapiInited || missingGoogleEnv) return;
    const gapi = (window as any).gapi;
    if (!gapi) return;
    console.log('Initializing gapi client', GOOGLE_CLIENT_ID, GOOGLE_API_KEY);
    gapi.load('client', async () => {
      try {
        await gapi.client.init({
          apiKey: GOOGLE_API_KEY,
          discoveryDocs: [
            // Calendar API discovery doc (used to find events containing Meet links)
            'https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest',
          ],
        });
        setGapiInited(true);
      } catch (e) {
        console.error('Failed to init gapi client', e);
      }
    });
  }, [gapiLoaded, gapiInited, missingGoogleEnv]);

  // Initialize GIS token client after script load
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!gisLoaded || !gapiInited || tokenClientRef.current || missingGoogleEnv) return;
    const googleObj = (window as any).google;
    const gapi = (window as any).gapi;
    if (!googleObj || !gapi) return;
    tokenClientRef.current = googleObj.accounts.oauth2.initTokenClient({
      client_id: GOOGLE_CLIENT_ID!,
      scope: 'https://www.googleapis.com/auth/calendar.readonly',
      callback: (resp: any) => {
        if (resp && resp.access_token) {
          setGoogleAccessToken(resp.access_token);
          gapi.client.setToken({ access_token: resp.access_token });
          // Persist token with a small buffer before expiry
          try {
            const expiresIn = Number(resp?.expires_in) || 3600; // seconds
            const expiresAt = Date.now() + Math.max(0, expiresIn - 60) * 1000; // buffer 60s
            sessionStorage.setItem(GOOGLE_TOKEN_KEY, resp.access_token);
            sessionStorage.setItem(GOOGLE_TOKEN_EXPIRES_AT_KEY, String(expiresAt));
          } catch (e) {
            console.error('Failed to persist Google token', e);
          }
        }
      },
      error_callback: (err: any) => {
        console.error('GIS error:', err);
      },
    });
  }, [gisLoaded, gapiInited, missingGoogleEnv]);

  const signInGoogle = useCallback(() => {
    if (missingGoogleEnv) return;
    if (!tokenClientRef.current) return;
    // Prefer silent if we appear to have prior consent/token
    const gapi = (typeof window !== 'undefined') ? (window as any).gapi : null;
    let storedToken: string | null = null;
    try { storedToken = sessionStorage.getItem(GOOGLE_TOKEN_KEY); } catch {}
    const hasToken = !!(googleAccessToken || gapi?.client?.getToken()?.access_token || storedToken);
    tokenClientRef.current.requestAccessToken({ prompt: hasToken ? '' : 'consent' });
  }, [googleAccessToken, missingGoogleEnv]);

  const ensureGoogleAuth = useCallback(async () => {
    const gapi = (window as any).gapi;
    // If we already have an access token in gapi or state, reuse it
    const existing = gapi?.client?.getToken()?.access_token || googleAccessToken;
    if (existing) return existing as string;

    // Try to hydrate from sessionStorage if not expired
    try {
      const stored = sessionStorage.getItem(GOOGLE_TOKEN_KEY);
      const exp = parseInt(sessionStorage.getItem(GOOGLE_TOKEN_EXPIRES_AT_KEY) || '0', 10);
      if (stored && exp && exp > Date.now()) {
        setGoogleAccessToken(stored);
        gapi?.client?.setToken?.({ access_token: stored });
        return stored;
      }
    } catch (e) {
      console.error('Failed to read persisted Google token', e);
    }

    // Otherwise, request one. Try silent first, then fall back to consent.
    await new Promise<void>((resolve) => {
      const tc = tokenClientRef.current;
      if (!tc) return resolve();

      let resolved = false;
      const persist = (accessToken: string, expiresIn?: number) => {
        try {
          const expiresInSec = Number(expiresIn) || 3600;
          const expiresAt = Date.now() + Math.max(0, expiresInSec - 60) * 1000;
          sessionStorage.setItem(GOOGLE_TOKEN_KEY, accessToken);
          sessionStorage.setItem(GOOGLE_TOKEN_EXPIRES_AT_KEY, String(expiresAt));
        } catch {}
      };

      const doRequest = (promptVal: '' | 'consent', prev: any) => {
        const prevCb = tc.callback;
        tc.callback = (resp: any) => {
          try {
            if (resp && resp.access_token) {
              setGoogleAccessToken(resp.access_token);
              gapi?.client?.setToken?.({ access_token: resp.access_token });
              persist(resp.access_token, resp?.expires_in);
            }
          } finally {
            tc.callback = prevCb;
            if (!resolved) {
              resolved = true;
              resolve();
            }
          }
        };
        try {
          tc.requestAccessToken({ prompt: promptVal });
        } catch {
          // If request throws synchronously, fall back immediately if possible
          if (promptVal === '' && !resolved) {
            doRequest('consent', prevCb);
          } else if (!resolved) {
            resolved = true;
            resolve();
          }
        }
      };

      // Start with silent attempt
      doRequest('', null);

      // Fallback to consent after a short grace period if not resolved
      setTimeout(() => {
        if (!resolved) {
          doRequest('consent', null);
        }
      }, 800);
    });

    return (
      (window as any).gapi?.client?.getToken()?.access_token || googleAccessToken || null
    );
  }, [googleAccessToken]);

  // Hydrate token from session storage on load (after gapi init)
  useEffect(() => {
    if (typeof window === 'undefined' || !gapiInited) return;
    try {
      const token = sessionStorage.getItem(GOOGLE_TOKEN_KEY);
      const exp = parseInt(sessionStorage.getItem(GOOGLE_TOKEN_EXPIRES_AT_KEY) || '0', 10);
      if (token && exp && exp > Date.now()) {
        setGoogleAccessToken(token);
        (window as any).gapi?.client?.setToken?.({ access_token: token });
      }
    } catch (e) {
      console.error('Failed to hydrate Google token from storage', e);
    }
  }, [gapiInited]);

  // Lookup Meet info by scanning Calendar events for a matching Meet link/code
  const searchMeetByCode = useCallback(async (inputCode: string) => {
    if (missingGoogleEnv) throw new Error('Google env is not configured');
    const gapi = (window as any).gapi;
    if (!gapi) throw new Error('Google API client not loaded');

    await ensureGoogleAuth();

    // Normalize input code (strip url, keep abc-defg-hijk)
    const codeFromInput = (() => {
      const code = (inputCode || '').trim();
      const m = code.match(/([a-z]{3}-[a-z]{4}-[a-z]{3})/i) || code.match(/([a-z]{3}-[a-z]{3}-[a-z]{3})/i);
      return (m ? m[1] : code).toLowerCase();
    })();

    // List calendars
    const calListResp = await gapi.client.calendar.calendarList.list({ maxResults: 100 });
    const calendars: Array<{ id: string; summary: string }> = (calListResp.result.items || []).map((c: any) => ({ id: c.id, summary: c.summary }));

    const now = Date.now();
    const tdelta = 30 * 24 * 60 * 60 * 1000;
    const timeMin = new Date(now - tdelta).toISOString();
    const timeMax = new Date(now).toISOString();

    // Search each calendar for events containing the code
    const searched: any[] = [];
    for (const cal of calendars) {
      try {
        const evResp = await gapi.client.calendar.events.list({
          calendarId: cal.id,
          maxResults: 50,
          singleEvents: true,
          orderBy: 'startTime',
          timeMin,
          timeMax,
          showDeleted: false,
          conferenceDataVersion: 1,
        });
        const items = evResp.result.items || [];
        console.log('Found', items.length, 'events in', cal.summary);
        for (const ev of items) {
          searched.push({ calendar: cal, event: ev });
        }
      } catch (e) {
        // Ignore calendars we can't read
        continue;
      }
    }

    const extractCode = (uri: string | undefined) => {
      if (!uri) return null;
      const m = uri.match(/meet\.google\.com\/(?:lookup\/)?([a-z\-]+)/i);
      return m ? m[1].toLowerCase() : null;
    };

    const matches = searched.filter(({ event }) => {
      const linkCode = extractCode(event.hangoutLink);
      const ep = event.conferenceData?.entryPoints || [];
      const epCodes: string[] = ep.map((p: any) => extractCode(p.uri)).filter(Boolean);
      return (
        (linkCode && linkCode.includes(codeFromInput)) ||
        epCodes.some((c) => (c as string).includes(codeFromInput))
      );
    });

    return {
      input: inputCode,
      normalizedCode: codeFromInput,
      matches: matches.map(({ calendar, event }) => ({
        calendar,
        event: {
          id: event.id,
          status: event.status,
          summary: event.summary,
          description: event.description,
          start: event.start,
          end: event.end,
          organizer: event.organizer,
          attendees: event.attendees,
          hangoutLink: event.hangoutLink,
          conferenceData: event.conferenceData,
          htmlLink: event.htmlLink,
        },
      })),
      searchedCalendars: calendars.length,
    };
  }, [ensureGoogleAuth, missingGoogleEnv]);

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
    <>
      {/* Load Google libraries on client */}
      <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" onLoad={() => setGisLoaded(true)} />
      <Script src="https://apis.google.com/js/api.js" strategy="afterInteractive" onLoad={() => setGapiLoaded(true)} />

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
                onClick={signInGoogle}
                style={{ 
                  background: googleAccessToken ? '#16a34a' : '#4285F4', 
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
                title={googleAccessToken ? 'Google Connected' : 'Connect Google'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                {googleAccessToken ? 'Google Connected' : 'Google'}
              </button>
              <button
                onClick={() => {
                  logout();
                  try {
                    sessionStorage.removeItem('google_access_token');
                    sessionStorage.removeItem('google_access_token_expires_at');
                  } catch {}
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

      {/* Navigation Tabs */}
      <nav style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #334155', paddingBottom: 8 }}>
          <div style={{ display: 'flex', borderBottom: '1px solid #334155', width: '100%' }}>
            <button
              onClick={() => setActiveTab('user')}
              style={{
                background: 'transparent',
                color: activeTab === 'user' ? '#fff' : '#94a3b8',
                border: 'none',
                borderBottom: activeTab === 'user' ? '2px solid #60a5fa' : '2px solid transparent',
                padding: '12px 24px',
                marginRight: '4px',
                cursor: 'pointer',
                fontSize: 16,
                fontWeight: activeTab === 'user' ? '600' : '400',
                transition: 'all 0.2s ease',
                position: 'relative',
                bottom: '-1px',
                borderRadius: '4px 4px 0 0',
                backgroundColor: activeTab === 'user' ? 'rgba(96, 165, 250, 0.1)' : 'transparent'
              }}
            >
              User
            </button>
            <button
              onClick={() => setActiveTab('meet')}
              style={{
                background: 'transparent',
                color: activeTab === 'meet' ? '#fff' : '#94a3b8',
                border: 'none',
                borderBottom: activeTab === 'meet' ? '2px solid #60a5fa' : '2px solid transparent',
                padding: '12px 24px',
                cursor: 'pointer',
                fontSize: 16,
                fontWeight: activeTab === 'meet' ? '600' : '400',
                transition: 'all 0.2s ease',
                position: 'relative',
                bottom: '-1px',
                borderRadius: '4px 4px 0 0',
                backgroundColor: activeTab === 'meet' ? 'rgba(96, 165, 250, 0.1)' : 'transparent'
              }}
            >
              Meet
            </button>
          </div>
        </div>
      </nav>

      {/* Content Sections */}
      {activeTab === 'user' && (
        <>
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
            {data && (() => {
              const u: any = (data as any)?.current_user ?? (data as any) ?? {};
              const displayName = u?.name || u?.username || 'Unknown user';
              const email = u?.email || '';
              const id = u?.id ?? '—';
              const username = u?.username ?? '—';
              const extId = u?.ext_id ?? '—';
              const groups = Array.isArray(u?.groups) ? (u.groups as any[]).join(', ') : (u?.groups || '—');

              return (
                <div>
                  <div style={{ fontSize: 18, marginBottom: 6 }}>
                    <span>{displayName}</span>
                    {email && (
                      <span style={{ color: '#94a3b8' }}> {'<'}{email}{'>'}</span>
                    )}
                  </div>
                  <div style={{ color: '#94a3b8', fontSize: '0.9em', lineHeight: 1.6 }}>
                    <div>id: {id}</div>
                    <div>username: {username}</div>
                    <div>ext_id: {extId}</div>
                    <div>groups: {groups}</div>
                  </div>
                </div>
              );
            })()}
          </section>
          <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16, marginTop: 16 }}>
            <TokenPanel />
          </section>
        </>
      )}

      {activeTab === 'meet' && (
        <section style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16 }}>
          <h2 style={{ fontSize: 20, marginTop: 0, marginBottom: 12 }}>Meet</h2>
          {missingGoogleEnv && (
            <p style={{ color: '#fca5a5' }}>
              Missing Google configuration. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID and NEXT_PUBLIC_GOOGLE_API_KEY in your environment.
            </p>
          )}
          <MeetForm 
            onSearch={searchMeetByCode} 
            missingGoogleEnv={missingGoogleEnv}
          />
        </section>
      )}

      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </main>
    </>
  )
}



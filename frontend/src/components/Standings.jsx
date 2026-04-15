import { useState, useEffect } from 'react'

const API = '/api'

const s = {
  wrap: { background: 'var(--surface)', borderRadius: 12, boxShadow: 'var(--shadow)', overflow: 'hidden' },
  header: { background: 'var(--dark)', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 12 },
  headerTitle: { fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--orange)', letterSpacing: '0.5px' },
  headerSub: { fontSize: 13, color: '#aaa' },
  headerActions: { display: 'flex', gap: 8 },
  refreshBtn: { background: 'none', border: '1px solid #555', borderRadius: 6, padding: '6px 14px', color: '#aaa', fontSize: 12, cursor: 'pointer' },
  rebuildBtn: { background: 'var(--orange)', border: '1px solid var(--orange)', borderRadius: 6, padding: '6px 14px', color: '#fff', fontSize: 12, cursor: 'pointer', fontWeight: 700 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th: { padding: '10px 14px', background: '#f5f5f5', fontWeight: 600, fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.4px', textAlign: 'center', borderBottom: '2px solid var(--border)' },
  thLeft: { textAlign: 'left' },
  td: { padding: '12px 14px', borderBottom: '1px solid var(--border)', textAlign: 'center' },
  tdLeft: { textAlign: 'left' },
  pos: (p) => ({ fontFamily: 'var(--font-display)', fontSize: 20, color: p === 1 ? 'var(--orange)' : p === 2 ? '#888' : p === 3 ? '#a0522d' : 'var(--muted)' }),
  bestPts: { fontFamily: 'var(--font-display)', fontSize: 20 },
  chip: (pts, counted) => ({
    display: 'inline-block', padding: '2px 7px', borderRadius: 4,
    fontSize: 11, fontFamily: 'var(--font-mono)',
    fontWeight: counted ? 700 : 400, margin: '1px 2px',
    background: counted ? (pts >= 9 ? 'var(--orange)' : pts >= 6 ? '#c8e6c9' : '#f0f0f0') : '#f5f5f5',
    color: counted ? (pts >= 9 ? '#fff' : pts >= 6 ? '#2e7d32' : 'var(--dark)') : '#bbb',
    textDecoration: counted ? 'none' : 'line-through',
  }),
  empty: { padding: 48, textAlign: 'center', color: 'var(--muted)' },
  loading: { padding: 48, textAlign: 'center', color: 'var(--muted)' },
  spinner: { display: 'inline-block', width: 20, height: 20, border: '3px solid #eee', borderTop: '3px solid var(--orange)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', marginRight: 10, verticalAlign: 'middle' },
  legend: { padding: '12px 24px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--muted)', display: 'flex', gap: 16, flexWrap: 'wrap' },
}

function getCountedFlags(allResults) {
  const n = allResults.length
  const count = Math.ceil(n / 2) + 1
  const sorted = [...allResults].sort((a, b) => b - a)
  const threshold = sorted[count - 1]
  let used = 0
  return allResults.map(pts => {
    if (pts > threshold || (pts === threshold && used < count)) { used++; return true }
    return false
  })
}

export default function Standings() {
  const [standings, setStandings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [rebuilding, setRebuilding] = useState(false)

  const fetch_ = async () => {
    setLoading(true); setError(null)
    try {
      const res = await fetch(`${API}/standings`)
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Failed')
      setStandings(json.standings || [])
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetch_() }, [])

  const rebuildSeason = async () => {
    const ok = window.confirm('Rebuild season from existing GameResults rows? This rewrites GameResults and Dashboard.')
    if (!ok) return

    setRebuilding(true)
    setError(null)
    try {
      const res = await fetch(`${API}/rebuild-season`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dry_run: false }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Rebuild failed')
      await fetch_()
    } catch (err) {
      setError(err.message)
    } finally {
      setRebuilding(false)
    }
  }

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <div style={s.headerLeft}>
          <span style={{ fontSize: 24 }}>🏅</span>
          <div>
            <div style={s.headerTitle}>2026 Season Standings</div>
            <div style={s.headerSub}>Best ½+1 results count{lastUpdated ? ` · Updated ${lastUpdated}` : ''}</div>
          </div>
        </div>
        <div style={s.headerActions}>
          <button style={s.refreshBtn} onClick={fetch_}>↻ Refresh</button>
          <button style={{ ...s.rebuildBtn, opacity: rebuilding ? 0.7 : 1 }} onClick={rebuildSeason} disabled={rebuilding}>
            {rebuilding ? 'Rebuilding…' : '♻ Rebuild From Scratch'}
          </button>
        </div>
      </div>

      {loading && <div style={s.loading}><span style={s.spinner} />Loading...</div>}
      {error && <div style={{ padding: 24, color: '#c62828' }}>❌ {error}</div>}
      {!loading && !error && standings.length === 0 && (
        <div style={s.empty}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🥏</div>
          <p>No rounds processed yet. Submit a round to see standings.</p>
        </div>
      )}

      {!loading && standings.length > 0 && (
        <>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={{ ...s.th, width: 60 }}>#</th>
                <th style={{ ...s.th, ...s.thLeft }}>Player</th>
                <th style={s.th}>Best ½+1 Pts</th>
                <th style={s.th}>YTD Pts</th>
                <th style={s.th}>Games</th>
                <th style={s.th}>All Results (bold = counted)</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((p, i) => {
                const flags = getCountedFlags(p.all_results)
                return (
                  <tr key={p.player} style={{ background: i % 2 === 0 ? '#fafafa' : '#fff' }}>
                    <td style={s.td}><span style={s.pos(p.position)}>{p.position === 1 ? '🥇' : p.position === 2 ? '🥈' : p.position === 3 ? '🥉' : p.position}</span></td>
                    <td style={{ ...s.td, ...s.tdLeft, fontWeight: 700 }}>{p.player}</td>
                    <td style={s.td}><span style={s.bestPts}>{p.best_half_plus_one}</span></td>
                    <td style={{ ...s.td, color: 'var(--muted)' }}>{p.champ_pts_ytd}</td>
                    <td style={{ ...s.td, fontFamily: 'var(--font-mono)' }}>{p.games_played}</td>
                    <td style={s.td}>
                      {p.all_results.map((pts, j) => <span key={j} style={s.chip(pts, flags[j])}>{pts}</span>)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div style={s.legend}>
            <span>🟠 Bold = counting toward standings</span>
            <span>Strikethrough = dropped</span>
            <span>Formula: best ⌈games/2⌉+1 results</span>
          </div>
        </>
      )}
    </div>
  )
}

const MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' }

const s = {
  wrap: { background: 'var(--surface)', borderRadius: 12, boxShadow: 'var(--shadow)', overflow: 'hidden' },
  header: { background: 'var(--dark)', padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12 },
  headerTitle: { fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--orange)', letterSpacing: '0.5px' },
  headerSub: { fontSize: 13, color: '#aaa' },
  multiplierBadge: { display: 'inline-block', background: 'var(--orange)', color: '#fff', borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 700, marginLeft: 8 },
  winner: { background: 'linear-gradient(135deg, #1a1a1a 0%, #2d1a00 100%)', padding: '24px', textAlign: 'center', borderBottom: '3px solid var(--orange)' },
  winnerLabel: { fontSize: 12, color: '#aaa', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 6 },
  winnerName: { fontFamily: 'var(--font-display)', fontSize: 42, color: 'var(--orange)', letterSpacing: '2px' },
  winnerScore: { fontSize: 14, color: '#ccc', marginTop: 4 },
  tiebreaker: { background: '#fff8e1', borderBottom: '1px solid #ffe082', padding: '10px 24px', fontSize: 13, color: '#7c5a00' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { padding: '9px 12px', background: '#f5f5f5', fontWeight: 600, fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.4px', textAlign: 'center', borderBottom: '2px solid var(--border)' },
  thLeft: { textAlign: 'left' },
  td: { padding: '10px 12px', borderBottom: '1px solid var(--border)', textAlign: 'center' },
  tdLeft: { textAlign: 'left' },
  pos: (p) => ({ fontFamily: 'var(--font-display)', fontSize: 18, color: p === 1 ? 'var(--orange)' : p === 2 ? '#888' : p === 3 ? '#a0522d' : 'var(--muted)' }),
  pts: (p) => ({ fontFamily: 'var(--font-display)', fontSize: 16, color: p >= 9 ? 'var(--orange)' : p >= 6 ? '#2e7d32' : 'var(--dark)' }),
  breakdown: { fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)' },
  actions: { padding: '20px 24px', display: 'flex', gap: 12 },
  nextBtn: { background: 'var(--green)', color: '#fff', border: 'none', borderRadius: 8, padding: '13px 28px', fontSize: 16, fontWeight: 700, cursor: 'pointer' },
}

function breakdown(p) {
  const parts = [`${p.raw_score} raw`]
  if (p.running_handicap) parts.push(`−${p.running_handicap} hcp`)
  if (p.strokes_of_honor) parts.push(`+${p.strokes_of_honor} honor`)
  if (p.prev_placement_pts) parts.push(`+${p.prev_placement_pts} placement`)
  if (p.new_player_bonus) parts.push(`−${p.new_player_bonus} new player`)
  return parts.join(' · ')
}

export default function RoundResults({ results, multiplier, tiebreaker_notes, onAddAnother }) {
  if (!results?.length) return null
  const winner = results.find(p => p.placement === 1)
  const hasTB = results.some(p => p.tiebreaker_used)

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <span style={{ fontSize: 24 }}>🏆</span>
        <div>
          <div style={s.headerTitle}>
            Round Results
            {multiplier > 1 && <span style={s.multiplierBadge}>{multiplier}× pts</span>}
          </div>
          <div style={s.headerSub}>Championship points awarded · Reference & Dashboard updated</div>
        </div>
      </div>

      {winner && (
        <div style={s.winner}>
          <div style={s.winnerLabel}>🥏 Round Winner</div>
          <div style={s.winnerName}>{winner.name}</div>
          <div style={s.winnerScore}>Adjusted: {winner.adjusted_score} · {winner.championship_pts_earned} championship pts</div>
        </div>
      )}

      {hasTB && (
        <div style={s.tiebreaker}>
          ⚖️ Tiebreaker applied{tiebreaker_notes?.length ? ': ' + tiebreaker_notes.join(' · ') : ''}
        </div>
      )}

      <table style={s.table}>
        <thead>
          <tr>
            <th style={{ ...s.th, ...s.thLeft }}>Place</th>
            <th style={{ ...s.th, ...s.thLeft }}>Player</th>
            <th style={s.th}>Adj Score</th>
            <th style={s.th}>Raw</th>
            <th style={s.th}>Handicap</th>
            <th style={s.th}>Game Diff</th>
            <th style={s.th}>Champ Pts</th>
            <th style={s.th}>Breakdown</th>
          </tr>
        </thead>
        <tbody>
          {results.map((p, i) => (
            <tr key={p.name} style={{ background: i % 2 === 0 ? '#fafafa' : '#fff' }}>
              <td style={{ ...s.td, ...s.tdLeft }}>
                <span style={s.pos(p.placement)}>{MEDALS[p.placement] || p.placement}</span>
                {p.tiebreaker_used && <span style={{ fontSize: 10, color: 'var(--orange)', marginLeft: 4 }}>TB</span>}
              </td>
              <td style={{ ...s.td, ...s.tdLeft, fontWeight: 600 }}>{p.name}</td>
              <td style={s.td}><strong style={{ fontFamily: 'var(--font-mono)', fontSize: 15 }}>{p.adjusted_score}</strong></td>
              <td style={{ ...s.td, color: 'var(--muted)', fontSize: 12 }}>{p.raw_score}</td>
              <td style={{ ...s.td, fontFamily: 'var(--font-mono)' }}>{p.running_handicap > 0 ? `−${p.running_handicap}` : '—'}</td>
              <td style={{ ...s.td, fontFamily: 'var(--font-mono)' }}>+{p.single_game_handicap}</td>
              <td style={s.td}><span style={s.pts(p.championship_pts_earned)}>{p.championship_pts_earned}</span></td>
              <td style={{ ...s.td, ...s.breakdown }}>{breakdown(p)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={s.actions}>
        <button style={s.nextBtn} onClick={onAddAnother}>+ Add Another Round</button>
      </div>
    </div>
  )
}

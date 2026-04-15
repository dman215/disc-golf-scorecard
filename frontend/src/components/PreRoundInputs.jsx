import { useState } from 'react'

const s = {
  wrap: { background: 'var(--surface)', borderRadius: 12, boxShadow: 'var(--shadow)', overflow: 'hidden' },
  header: { background: 'var(--dark)', padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12 },
  headerTitle: { fontFamily: 'var(--font-display)', fontSize: 22, color: 'var(--orange)', letterSpacing: '0.5px' },
  headerSub: { fontSize: 13, color: '#aaa' },
  section: { padding: '20px 24px', borderBottom: '1px solid var(--border)' },
  sectionTitle: { fontFamily: 'var(--font-display)', fontSize: 16, letterSpacing: '0.5px', color: 'var(--dark)', marginBottom: 14 },
  multiplierRow: { display: 'flex', gap: 10, flexWrap: 'wrap' },
  multiplierBtn: (active) => ({
    padding: '10px 22px', borderRadius: 8,
    border: active ? '2px solid var(--orange)' : '2px solid var(--border)',
    background: active ? 'var(--orange)' : '#fff',
    color: active ? '#fff' : 'var(--dark)',
    fontFamily: 'var(--font-display)', fontSize: 18, cursor: 'pointer', transition: 'all 0.15s',
  }),
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th: { padding: '8px 12px', textAlign: 'left', fontWeight: 600, fontSize: 12, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.4px', borderBottom: '2px solid var(--border)' },
  thCenter: { textAlign: 'center' },
  td: { padding: '10px 12px', borderBottom: '1px solid var(--border)' },
  tdCenter: { textAlign: 'center' },
  toggle: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 },
  toggleBtn: (active) => ({
    width: 36, height: 36, borderRadius: 6,
    border: active ? '2px solid var(--orange)' : '2px solid var(--border)',
    background: active ? 'var(--orange)' : '#fff',
    color: active ? '#fff' : 'var(--muted)',
    fontSize: 16, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s',
  }),
  select: { border: '1px solid var(--border)', borderRadius: 6, padding: '6px 8px', fontSize: 14, fontFamily: 'var(--font-body)', background: '#fff', cursor: 'pointer', minWidth: 80 },
  actions: { padding: '20px 24px', display: 'flex', gap: 12 },
  submitBtn: { background: 'var(--orange)', color: '#fff', border: 'none', borderRadius: 8, padding: '13px 28px', fontSize: 16, fontWeight: 700, cursor: 'pointer' },
  backBtn: { background: 'none', border: '1.5px solid var(--border)', borderRadius: 8, padding: '12px 24px', fontSize: 14, color: 'var(--mid)', fontWeight: 500, cursor: 'pointer' },
  hint: { padding: '12px 24px', borderTop: '1px dashed var(--border)', fontSize: 12, color: 'var(--muted)' },
}

const MULTIPLIERS = [1, 1.5, 2]

export default function PreRoundInputs({ players, onSubmit, onBack }) {
  const [multiplier, setMultiplier] = useState(1)
  const [playerData, setPlayerData] = useState(() =>
    players.map((name, i) => ({
      name,
      mulligan_type: 'yes',
      mulligan_used: true,
      metal_hits: 0,
      arrival_order: i + 1,
      new_players_brought: 0,
    }))
  )

  const update = (index, field, value) =>
    setPlayerData(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p))

  const arrivalOptions = players.map((_, i) => i + 1)

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <span style={{ fontSize: 24 }}>🏆</span>
        <div>
          <div style={s.headerTitle}>Pre-Round Details</div>
          <div style={s.headerSub}>Required for tiebreakers & bonuses</div>
        </div>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>Championship Point Multiplier</div>
        <div style={s.multiplierRow}>
          {MULTIPLIERS.map(m => (
            <button type="button" key={m} style={s.multiplierBtn(multiplier === m)} onClick={() => setMultiplier(m)}>{m}×</button>
          ))}
        </div>
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>1× regular · 1.5× special event · 2× season opener / solstice</p>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>Player Details</div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Player</th>
              <th style={{ ...s.th, ...s.thCenter }}>Mulligan Used?</th>
              <th style={{ ...s.th, ...s.thCenter }}>Metal Hits</th>
              <th style={{ ...s.th, ...s.thCenter }}>Arrival Order</th>
              <th style={{ ...s.th, ...s.thCenter }}>New Players Brought</th>
            </tr>
          </thead>
          <tbody>
            {playerData.map((p, i) => (
              <tr key={p.name} style={{ background: i % 2 === 0 ? '#fafafa' : '#fff' }}>
                <td style={{ ...s.td, fontWeight: 600 }}>{p.name}</td>
                <td style={{ ...s.td, ...s.tdCenter }}>
                <div style={s.toggle}>
                  <button
                    type="button"
                    style={s.toggleBtn(p.mulligan_type === 'no')}
                    onClick={() => setPlayerData(prev => prev.map((row, pi) => pi === i ? { ...row, mulligan_type: 'no', mulligan_used: false } : row))}
                  >
                    No
                  </button>
                  <button
                    type="button"
                    style={s.toggleBtn(p.mulligan_type === 'yes')}
                    onClick={() => setPlayerData(prev => prev.map((row, pi) => pi === i ? { ...row, mulligan_type: 'yes', mulligan_used: true } : row))}
                  >
                    Yes
                  </button>
                  <button
                    type="button"
                    style={s.toggleBtn(p.mulligan_type === 'va')}
                    onClick={() => setPlayerData(prev => prev.map((row, pi) => pi === i ? { ...row, mulligan_type: 'va', mulligan_used: true } : row))}
                  >
                    VA
                  </button>
                </div>
                </td>
                <td style={{ ...s.td, ...s.tdCenter }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                    <button type="button" style={{ ...s.toggleBtn(false), width: 28, height: 28 }} onClick={() => update(i, 'metal_hits', Math.max(0, p.metal_hits - 1))}>−</button>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, minWidth: 20, textAlign: 'center' }}>{p.metal_hits}</span>
                    <button type="button" style={{ ...s.toggleBtn(false), width: 28, height: 28 }} onClick={() => update(i, 'metal_hits', p.metal_hits + 1)}>+</button>
                  </div>
                </td>
                <td style={{ ...s.td, ...s.tdCenter }}>
                  <select style={s.select} value={p.arrival_order} onChange={e => update(i, 'arrival_order', parseInt(e.target.value))}>
                    {arrivalOptions.map(n => <option key={n} value={n}>{n}{n === 1 ? ' (first)' : n === players.length ? ' (last)' : ''}</option>)}
                  </select>
                </td>
                <td style={{ ...s.td, ...s.tdCenter }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                    <button type="button" style={{ ...s.toggleBtn(false), width: 28, height: 28 }} onClick={() => update(i, 'new_players_brought', Math.max(0, p.new_players_brought - 1))}>−</button>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, minWidth: 20, textAlign: 'center' }}>{p.new_players_brought}</span>
                    <button type="button" style={{ ...s.toggleBtn(false), width: 28, height: 28 }} onClick={() => update(i, 'new_players_brought', p.new_players_brought + 1)}>+</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={s.hint}>💡 "New Players Brought" = first-time-ever league members you invited. Gives you −1 stroke per new player this round.</div>
      </div>

      <div style={s.actions}>
        <button type="button" style={s.submitBtn} onClick={() => onSubmit({ multiplier, players: playerData })}>→ Process Round</button>
        <button type="button" style={s.backBtn} onClick={onBack}>← Back to Scores</button>
      </div>
    </div>
  )
}

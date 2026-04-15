import { useState } from 'react'

const s = {
  wrap: { overflowX: 'auto', borderRadius: 10, border: '1px solid var(--border)', background: '#fff' },
  table: { borderCollapse: 'collapse', width: '100%', fontSize: 13, fontFamily: 'var(--font-mono)' },
  th: {
    padding: '8px 10px', background: 'var(--dark)', color: '#fff',
    fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: 12,
    textAlign: 'center', whiteSpace: 'nowrap',
  },
  thLeft: { textAlign: 'left', paddingLeft: 14 },
  td: { padding: '7px 8px', textAlign: 'center', borderBottom: '1px solid var(--border)', color: 'var(--dark)' },
  tdName: { textAlign: 'left', paddingLeft: 14, fontFamily: 'var(--font-body)', fontWeight: 600, whiteSpace: 'nowrap' },
  tdPar: { background: '#f0f0f0', color: 'var(--muted)', fontWeight: 600 },
  input: {
    width: 36, textAlign: 'center', border: '1px solid var(--border)',
    borderRadius: 4, padding: '3px 0', fontFamily: 'var(--font-mono)',
    fontSize: 13, background: 'transparent',
  },
  ace: { background: 'var(--blue-ace)', color: '#fff', borderRadius: 50, width: 28, height: 28, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 },
  over: { background: 'var(--orange-light)', borderRadius: 4, display: 'inline-block', width: 28, textAlign: 'center', padding: '2px 0' },
  overDouble: { background: 'var(--orange)', color: '#fff', borderRadius: 4, display: 'inline-block', width: 28, textAlign: 'center', padding: '2px 0' },
  birdie: { color: 'var(--green)', fontWeight: 700 },
  meta: { padding: '14px 16px', borderBottom: '1px solid var(--border)', display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center' },
  metaItem: { display: 'flex', flexDirection: 'column', gap: 2 },
  metaLabel: { fontSize: 10, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' },
  metaValue: { fontSize: 15, fontWeight: 600, color: 'var(--dark)' },
  metaInput: { border: '1px solid var(--border)', borderRadius: 4, padding: '4px 8px', fontSize: 14, fontWeight: 600, width: 140 },
  metaSelect: { border: '1px solid var(--border)', borderRadius: 4, padding: '4px 8px', fontSize: 14, fontWeight: 600, width: 160, background: '#fff' },
  warnings: { padding: '10px 14px', background: '#fff8e1', borderBottom: '1px solid #ffe082', fontSize: 13, color: '#7c5a00' },
}

const SKY_OPTIONS = [
  { value: '', label: 'Unknown' },
  { value: 'sunny', label: 'Sunny' },
  { value: 'partly_cloudy', label: 'Partly Cloudy' },
  { value: 'cloudy', label: 'Cloudy' },
  { value: 'mostly_cloudy', label: 'Mostly Cloudy' },
  { value: 'rain', label: 'Rain' },
  { value: 'snow', label: 'Snow' },
]

function ScoreCell({ score, par, isAce }) {
  if (score === null || score === undefined || score === '') {
    return <span style={{ color: '#ccc' }}>—</span>
  }
  if (isAce) {
    return <span style={s.ace}>{score}</span>
  }
  const diff = score - par
  if (diff <= -1) return <span style={s.birdie}>{score}</span>
  if (diff === 1) return <span style={s.over}>{score}</span>
  if (diff >= 2) return <span style={s.overDouble}>{score}</span>
  return <span>{score}</span>
}

export default function ScorecardTable({ data, onChange }) {
  const [editingCell, setEditingCell] = useState(null) // { playerIdx, holeIdx }

  if (!data) return null

  const { course, tees, date, location, skies, par_total, hole_pars = [], players = [] } = data
  const holes = Array.from({ length: 18 }, (_, i) => i + 1)

  const handleMetaChange = (field, value) => {
    onChange({ ...data, [field]: value })
  }

  const handleScoreChange = (playerIdx, holeIdx, value) => {
    const updated = { ...data }
    updated.players = updated.players.map((p, pi) => {
      if (pi !== playerIdx) return p
      const scores = [...(p.scores || [])]
      scores[holeIdx] = value === '' ? null : parseInt(value, 10) || null
      // Recompute total
      const total = scores.reduce((sum, s) => sum + (s || 0), 0)
      const playedPar = hole_pars.reduce((sum, p, i) =>
        scores[i] !== null && scores[i] !== undefined ? sum + p : sum, 0)
      return { ...p, scores, total, plus_minus: total - playedPar }
    })
    onChange(updated)
  }

  return (
    <div style={s.wrap}>
      {/* Meta row */}
      <div style={s.meta}>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Course</span>
          <input style={s.metaInput} value={course || ''} onChange={e => handleMetaChange('course', e.target.value)} />
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Tees</span>
          <input style={{ ...s.metaInput, width: 120 }} value={tees || ''} onChange={e => handleMetaChange('tees', e.target.value)} />
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Date</span>
          <input style={{ ...s.metaInput, width: 130 }} value={date || ''} onChange={e => handleMetaChange('date', e.target.value)} />
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Location</span>
          <input style={{ ...s.metaInput, width: 180 }} value={location || ''} onChange={e => handleMetaChange('location', e.target.value)} />
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Skies</span>
          <select
            style={s.metaSelect}
            value={skies || ''}
            onChange={e => handleMetaChange('skies', e.target.value)}
          >
            {SKY_OPTIONS.map(option => (
              <option key={option.value || 'unknown'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Par</span>
          <span style={s.metaValue}>{par_total}</span>
        </div>
        <div style={s.metaItem}>
          <span style={s.metaLabel}>Players</span>
          <span style={s.metaValue}>{players.length}</span>
        </div>
      </div>

      {/* Warnings */}
      {data._warnings?.length > 0 && (
        <div style={s.warnings}>
          ⚠️ {data._warnings.join(' · ')}
        </div>
      )}

      {/* Score grid */}
      <table style={s.table}>
        <thead>
          <tr>
            <th style={{ ...s.th, ...s.thLeft }}>Player</th>
            {holes.map(h => <th key={h} style={s.th}>{h}</th>)}
            <th style={s.th}>Total</th>
            <th style={s.th}>+/-</th>
          </tr>
          <tr>
            <th style={{ ...s.th, ...s.thLeft, background: '#333', fontSize: 11 }}>Par</th>
            {hole_pars.map((par, i) => (
              <th key={i} style={{ ...s.th, background: '#333', fontSize: 11 }}>{par}</th>
            ))}
            <th style={{ ...s.th, background: '#333', fontSize: 11 }}>{par_total}</th>
            <th style={{ ...s.th, background: '#333', fontSize: 11 }}>E</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player, pi) => (
            <tr key={pi} style={{ background: pi % 2 === 0 ? '#fafafa' : '#fff' }}>
              <td style={{ ...s.td, ...s.tdName }}>{player.name}</td>
              {holes.map((_, hi) => {
                const score = player.scores?.[hi]
                const par = hole_pars[hi] || 3
                const isAce = player.aces?.includes(hi + 1)
                const isEditing = editingCell?.playerIdx === pi && editingCell?.holeIdx === hi

                return (
                  <td key={hi} style={s.td}>
                    {isEditing ? (
                      <input
                        style={s.input}
                        defaultValue={score ?? ''}
                        autoFocus
                        onBlur={(e) => {
                          handleScoreChange(pi, hi, e.target.value)
                          setEditingCell(null)
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === 'Tab') {
                            handleScoreChange(pi, hi, e.target.value)
                            setEditingCell(null)
                          }
                        }}
                      />
                    ) : (
                      <span
                        style={{ cursor: 'pointer' }}
                        onClick={() => setEditingCell({ playerIdx: pi, holeIdx: hi })}
                        title="Click to edit"
                      >
                        <ScoreCell score={score} par={par} isAce={isAce} />
                      </span>
                    )}
                  </td>
                )
              })}
              <td style={{ ...s.td, fontWeight: 700 }}>{player.total ?? '—'}</td>
              <td style={{
                ...s.td, fontWeight: 700,
                color: (player.plus_minus > 0) ? 'var(--orange-dark)' : player.plus_minus < 0 ? 'var(--green)' : 'var(--dark)'
              }}>
                {player.plus_minus != null
                  ? (player.plus_minus > 0 ? `+${player.plus_minus}` : player.plus_minus)
                  : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ padding: '8px 14px', fontSize: 11, color: 'var(--muted)' }}>
        💡 Click any score to edit it before submitting
      </div>
    </div>
  )
}

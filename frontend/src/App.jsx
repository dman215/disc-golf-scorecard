import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import ScorecardTable from './components/ScorecardTable'
import PreRoundInputs from './components/PreRoundInputs'
import RoundResults from './components/RoundResults'
import Standings from './components/Standings'

const API = '/api'

const STEPS = {
  UPLOAD: 'upload',
  PARSING: 'parsing',
  REVIEW: 'review',
  PRE_ROUND: 'pre_round',
  PROCESSING: 'processing',
  SUCCESS: 'success',
}

const STEP_LABELS = ['① Upload', '② Parse', '③ Review Scores', '④ Round Details', '⑤ Results']
const STEP_KEYS = [STEPS.UPLOAD, STEPS.PARSING, STEPS.REVIEW, STEPS.PRE_ROUND, STEPS.SUCCESS]
const NAV = { SUBMIT: 'submit', STANDINGS: 'standings' }

const st = {
  app: { minHeight: '100vh', background: 'var(--bg)', fontFamily: 'var(--font-body)' },
  header: {
    background: 'var(--dark)', color: '#fff', padding: '0 32px',
    display: 'flex', alignItems: 'center', height: 60, gap: 14,
    justifyContent: 'space-between',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 14 },
  headerTitle: { fontFamily: 'var(--font-display)', fontSize: 28, letterSpacing: '1px', color: 'var(--orange)' },
  headerSub: { fontSize: 13, color: '#aaa' },
  navTabs: { display: 'flex', gap: 4 },
  navTab: (active) => ({
    padding: '8px 18px', borderRadius: 6,
    background: active ? 'var(--orange)' : 'transparent',
    color: active ? '#fff' : '#aaa',
    border: 'none', cursor: 'pointer', fontSize: 13,
    fontWeight: active ? 700 : 400, fontFamily: 'var(--font-body)',
    transition: 'all 0.15s',
  }),
  main: { maxWidth: 1200, margin: '0 auto', padding: '32px 24px' },
  stepBar: {
    display: 'flex', marginBottom: 28, background: 'var(--surface)',
    borderRadius: 10, overflow: 'hidden', boxShadow: 'var(--shadow)',
  },
  step: (active, done) => ({
    flex: 1, padding: '13px 8px', textAlign: 'center', fontSize: 12,
    fontWeight: done ? 600 : active ? 700 : 400,
    color: done ? 'var(--green)' : active ? 'var(--orange)' : 'var(--muted)',
    borderBottom: active ? '3px solid var(--orange)' : done ? '3px solid var(--green)' : '3px solid transparent',
    transition: 'all 0.2s',
  }),
  card: { background: 'var(--surface)', borderRadius: 12, boxShadow: 'var(--shadow)', padding: 28, marginBottom: 24 },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start', marginBottom: 24 },
  imageCard: { background: 'var(--surface)', borderRadius: 12, boxShadow: 'var(--shadow)', overflow: 'hidden' },
  imageCardHeader: { padding: '12px 16px', borderBottom: '1px solid var(--border)', fontSize: 13, fontWeight: 600, color: 'var(--muted)' },
  imagePreview: { width: '100%', objectFit: 'contain', maxHeight: 420, display: 'block' },
  sectionTitle: { fontFamily: 'var(--font-display)', fontSize: 20, color: 'var(--dark)', letterSpacing: '0.5px', marginBottom: 0 },
  parseBtn: {
    background: 'var(--orange)', color: '#fff', border: 'none',
    borderRadius: 8, padding: '13px 28px', fontSize: 16,
    fontWeight: 700, width: '100%', marginTop: 16, cursor: 'pointer',
  },
  confirmBtn: {
    background: 'var(--orange)', color: '#fff', border: 'none',
    borderRadius: 8, padding: '13px 28px', fontSize: 16, fontWeight: 700, cursor: 'pointer',
  },
  backBtn: {
    background: 'none', border: '1.5px solid var(--border)',
    borderRadius: 8, padding: '12px 24px', fontSize: 14,
    color: 'var(--mid)', fontWeight: 500, cursor: 'pointer',
  },
  actions: { display: 'flex', gap: 12, marginTop: 20, alignItems: 'center', flexWrap: 'wrap' },
  overwriteToggle: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--muted)', marginLeft: 'auto' },
  spinner: {
    display: 'inline-block', width: 22, height: 22,
    border: '3px solid #eee', borderTop: '3px solid var(--orange)',
    borderRadius: '50%', animation: 'spin 0.8s linear infinite',
    marginRight: 10, verticalAlign: 'middle',
  },
  error: { background: '#fff3f3', border: '1px solid #ffcdd2', borderRadius: 10, padding: 16, color: '#c62828', fontSize: 14, marginTop: 16 },
  warningBadge: { display: 'inline-block', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 6, padding: '3px 10px', fontSize: 12, color: '#7c5a00', marginLeft: 10 },
}

export default function App() {
  const [nav, setNav] = useState(NAV.SUBMIT)
  const [step, setStep] = useState(STEPS.UPLOAD)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null)
  const [parsedData, setParsedData] = useState(null)
  const [warnings, setWarnings] = useState([])
  const [overwrite, setOverwrite] = useState(false)
  const [roundResults, setRoundResults] = useState(null)
  const [error, setError] = useState(null)

  const currentStepIdx = STEP_KEYS.indexOf(step)

  const handleImageSelected = (file) => {
    setImageFile(file)
    setImagePreviewUrl(URL.createObjectURL(file))
    setError(null)
  }

  const handleParse = async () => {
    if (!imageFile) return
    setStep(STEPS.PARSING)
    setError(null)
    const formData = new FormData()
    formData.append('file', imageFile)
    try {
      const res = await fetch(`${API}/parse-scorecard`, { method: 'POST', body: formData })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Parse failed')
      setParsedData({ ...json.data, _warnings: json.warnings || [] })
      setWarnings(json.warnings || [])
      setStep(STEPS.REVIEW)
    } catch (err) {
      setError(err.message)
      setStep(STEPS.UPLOAD)
    }
  }

  const handleConfirmScores = async () => {
    setError(null)
    try {
      const res = await fetch(`${API}/write-to-sheet`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parsed_data: parsedData, overwrite }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Sheet write failed')
    } catch (err) {
      setError(err.message)
      return
    }
    setStep(STEPS.PRE_ROUND)
  }

  const handleProcessRound = async ({ multiplier, players: playerInputs }) => {
    setStep(STEPS.PROCESSING)
    setError(null)
    try {
      const res = await fetch(`${API}/process-round`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parsed_data: parsedData, multiplier, players: playerInputs }),
      })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Processing failed')
      setRoundResults(json)
      setStep(STEPS.SUCCESS)
    } catch (err) {
      setError(err.message)
      setStep(STEPS.PRE_ROUND)
    }
  }

  const handleReset = () => {
    setStep(STEPS.UPLOAD)
    setImageFile(null)
    setImagePreviewUrl(null)
    setParsedData(null)
    setWarnings([])
    setRoundResults(null)
    setError(null)
  }

  const playerNames = parsedData?.players?.map(p => p.name) || []

  return (
    <div style={st.app}>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>

      <header style={st.header}>
        <div style={st.headerLeft}>
          <span style={{ fontSize: 26 }}>🥏</span>
          <span style={st.headerTitle}>FUFA DISC GOLF LEAGUE</span>
          <span style={st.headerSub}>2026 Season</span>
        </div>
        <div style={st.navTabs}>
          <button style={st.navTab(nav === NAV.SUBMIT)} onClick={() => setNav(NAV.SUBMIT)}>Submit Round</button>
          <button style={st.navTab(nav === NAV.STANDINGS)} onClick={() => setNav(NAV.STANDINGS)}>🏅 Standings</button>
        </div>
      </header>

      <main style={st.main}>

        {/* STANDINGS */}
        {nav === NAV.STANDINGS && <Standings />}

        {/* SUBMIT ROUND */}
        {nav === NAV.SUBMIT && (
          <>
            {/* Step bar */}
            <div style={st.stepBar}>
              {STEP_LABELS.map((label, i) => (
                <div key={i} style={st.step(i === currentStepIdx, i < currentStepIdx)}>
                  {i < currentStepIdx ? '✓ ' : ''}{label}
                </div>
              ))}
            </div>

            {/* UPLOAD */}
            {(step === STEPS.UPLOAD || step === STEPS.PARSING) && (
              <div style={st.card}>
                <h2 style={{ ...st.sectionTitle, marginBottom: 16 }}>Upload Scorecard</h2>
                <ImageUploader onImageSelected={handleImageSelected} />
                {error && <div style={st.error}>❌ {error}</div>}
                <button
                  style={{ ...st.parseBtn, opacity: (!imageFile || step === STEPS.PARSING) ? 0.6 : 1, cursor: (!imageFile || step === STEPS.PARSING) ? 'not-allowed' : 'pointer' }}
                  onClick={handleParse}
                  disabled={!imageFile || step === STEPS.PARSING}
                >
                  {step === STEPS.PARSING
                    ? <><span style={st.spinner} />Parsing with Claude Vision...</>
                    : '→ Parse Scorecard'}
                </button>
              </div>
            )}

            {/* REVIEW — side by side: image | parsed table */}
            {step === STEPS.REVIEW && parsedData && (
              <>
                <div style={st.twoCol}>
                  {/* Scorecard image */}
                  <div style={st.imageCard}>
                    <div style={st.imageCardHeader}>📸 Original Scorecard — use this to validate</div>
                    <img src={imagePreviewUrl} alt="Scorecard" style={st.imagePreview} />
                  </div>

                  {/* Parsed table */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                      <h2 style={st.sectionTitle}>Parsed Scores</h2>
                      {warnings.length > 0 && (
                        <span style={st.warningBadge}>⚠️ {warnings.length} warning{warnings.length > 1 ? 's' : ''}</span>
                      )}
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 14 }}>
                      Click any score to edit before confirming.
                    </p>
                    <ScorecardTable data={parsedData} onChange={setParsedData} />
                    <div style={st.actions}>
                      <button style={st.confirmBtn} onClick={handleConfirmScores}>
                        ✓ Scores Look Good →
                      </button>
                      <button style={st.backBtn} onClick={handleReset}>← Start Over</button>
                      <label style={st.overwriteToggle}>
                        <input type="checkbox" checked={overwrite} onChange={e => setOverwrite(e.target.checked)} />
                        Overwrite existing
                      </label>
                    </div>
                    {error && <div style={st.error}>❌ {error}</div>}
                  </div>
                </div>
              </>
            )}

            {/* PRE-ROUND INPUTS */}
            {step === STEPS.PRE_ROUND && (
              <>
                <PreRoundInputs
                  players={playerNames}
                  onSubmit={handleProcessRound}
                  onBack={() => setStep(STEPS.REVIEW)}
                />
                {error && <div style={{ ...st.error, marginTop: 16 }}>❌ {error}</div>}
              </>
            )}

            {/* PROCESSING */}
            {step === STEPS.PROCESSING && (
              <div style={{ ...st.card, textAlign: 'center', padding: 48 }}>
                <span style={st.spinner} />
                <span style={{ fontSize: 16, color: 'var(--mid)' }}>
                  Calculating handicaps, placements & championship points...
                </span>
              </div>
            )}

            {/* SUCCESS */}
            {step === STEPS.SUCCESS && roundResults && (
              <RoundResults
                results={roundResults.results}
                multiplier={roundResults.multiplier}
                tiebreaker_notes={roundResults.tiebreaker_notes}
                onAddAnother={handleReset}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}

import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import ScorecardTable from './components/ScorecardTable'
import SubmitPanel from './components/SubmitPanel'

const API = '/api'

const STEPS = {
  UPLOAD: 'upload',
  PARSING: 'parsing',
  REVIEW: 'review',
  SUBMITTING: 'submitting',
  SUCCESS: 'success',
  ERROR: 'error',
}

const styles = {
  app: { minHeight: '100vh', background: 'var(--bg)', fontFamily: 'var(--font-body)' },

  header: {
    background: 'var(--dark)',
    color: '#fff',
    padding: '0 32px',
    display: 'flex',
    alignItems: 'center',
    height: 60,
    gap: 14,
  },
  headerTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: 28,
    letterSpacing: '1px',
    color: 'var(--orange)',
  },
  headerSub: { fontSize: 13, color: '#aaa', marginLeft: 4 },

  main: { maxWidth: 1100, margin: '0 auto', padding: '36px 24px' },

  card: {
    background: 'var(--surface)',
    borderRadius: 12,
    boxShadow: 'var(--shadow)',
    padding: 28,
    marginBottom: 24,
  },

  sectionTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: 22,
    color: 'var(--dark)',
    letterSpacing: '0.5px',
    marginBottom: 16,
  },

  stepBar: {
    display: 'flex',
    gap: 0,
    marginBottom: 32,
    background: 'var(--surface)',
    borderRadius: 10,
    overflow: 'hidden',
    boxShadow: 'var(--shadow)',
  },
  step: (active, done) => ({
    flex: 1,
    padding: '14px 8px',
    textAlign: 'center',
    fontSize: 13,
    fontWeight: done ? 600 : active ? 700 : 400,
    color: done ? 'var(--green)' : active ? 'var(--orange)' : 'var(--muted)',
    borderBottom: active ? '3px solid var(--orange)' : done ? '3px solid var(--green)' : '3px solid transparent',
    transition: 'all 0.2s',
  }),

  parseBtn: {
    background: 'var(--orange)',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '13px 28px',
    fontSize: 16,
    fontWeight: 700,
    width: '100%',
    marginTop: 16,
    letterSpacing: '0.3px',
    transition: 'background 0.2s',
  },

  spinner: {
    display: 'inline-block',
    width: 22,
    height: 22,
    border: '3px solid #eee',
    borderTop: '3px solid var(--orange)',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
    marginRight: 10,
    verticalAlign: 'middle',
  },

  success: {
    background: '#e8f5e9',
    border: '1px solid #a5d6a7',
    borderRadius: 10,
    padding: 24,
    textAlign: 'center',
  },
  successTitle: { fontSize: 22, fontWeight: 700, color: '#2e7d32', marginBottom: 8, fontFamily: 'var(--font-display)', letterSpacing: '0.5px' },
  successLink: { color: 'var(--orange)', fontWeight: 600, fontSize: 14 },

  error: {
    background: '#fff3f3',
    border: '1px solid #ffcdd2',
    borderRadius: 10,
    padding: 20,
    color: '#c62828',
    fontSize: 14,
  },

  warningBadge: {
    display: 'inline-block',
    background: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: 6,
    padding: '4px 10px',
    fontSize: 12,
    color: '#7c5a00',
    marginLeft: 10,
  },
}

const STEP_LABELS = ['① Upload', '② Parse', '③ Review', '④ Submit']
const STEP_KEYS = [STEPS.UPLOAD, STEPS.PARSING, STEPS.REVIEW, STEPS.SUCCESS]

function stepIndex(step) {
  return STEP_KEYS.indexOf(step)
}

export default function App() {
  const [step, setStep] = useState(STEPS.UPLOAD)
  const [imageFile, setImageFile] = useState(null)
  const [parsedData, setParsedData] = useState(null)
  const [warnings, setWarnings] = useState([])
  const [overwrite, setOverwrite] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const currentStepIdx = stepIndex(step)

  const handleImageSelected = (file) => {
    setImageFile(file)
    setError(null)
  }

  const handleParse = async () => {
    if (!imageFile) return
    setStep(STEPS.PARSING)
    setError(null)

    const formData = new FormData()
    formData.append('file', imageFile)

    try {
      const res = await fetch(`${API}/parse-scorecard`, {
        method: 'POST',
        body: formData,
      })
      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.detail || 'Parse failed')
      }

      const data = { ...json.data, _warnings: json.warnings || [] }
      setParsedData(data)
      setWarnings(json.warnings || [])
      setStep(STEPS.REVIEW)
    } catch (err) {
      setError(err.message)
      setStep(STEPS.UPLOAD)
    }
  }

  const handleSubmit = async () => {
    setStep(STEPS.SUBMITTING)
    setError(null)

    try {
      const res = await fetch(`${API}/write-to-sheet`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parsed_data: parsedData, overwrite }),
      })
      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.detail || 'Submit failed')
      }

      setResult(json)
      setStep(STEPS.SUCCESS)
    } catch (err) {
      setError(err.message)
      setStep(STEPS.REVIEW)
    }
  }

  const handleReset = () => {
    setStep(STEPS.UPLOAD)
    setImageFile(null)
    setParsedData(null)
    setWarnings([])
    setResult(null)
    setError(null)
  }

  return (
    <div style={styles.app}>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>

      <header style={styles.header}>
        <span style={{ fontSize: 26 }}>🥏</span>
        <span style={styles.headerTitle}>FUFA DISC GOLF LEAGUE</span>
        <span style={styles.headerSub}>2026 Season Tracker</span>
      </header>

      <main style={styles.main}>

        {/* Step bar */}
        <div style={styles.stepBar}>
          {STEP_LABELS.map((label, i) => (
            <div key={i} style={styles.step(i === currentStepIdx, i < currentStepIdx)}>
              {i < currentStepIdx ? '✓ ' : ''}{label}
            </div>
          ))}
        </div>

        {/* UPLOAD step */}
        {(step === STEPS.UPLOAD || step === STEPS.PARSING) && (
          <div style={styles.card}>
            <h2 style={styles.sectionTitle}>Upload Scorecard</h2>
            <ImageUploader onImageSelected={handleImageSelected} />

            {error && (
              <div style={{ ...styles.error, marginTop: 16 }}>
                ❌ {error}
              </div>
            )}

            <button
              style={{
                ...styles.parseBtn,
                opacity: (!imageFile || step === STEPS.PARSING) ? 0.6 : 1,
                cursor: (!imageFile || step === STEPS.PARSING) ? 'not-allowed' : 'pointer',
              }}
              onClick={handleParse}
              disabled={!imageFile || step === STEPS.PARSING}
            >
              {step === STEPS.PARSING ? (
                <><span style={styles.spinner} />Parsing scorecard with Claude Vision...</>
              ) : (
                '→ Parse Scorecard'
              )}
            </button>
          </div>
        )}

        {/* REVIEW step */}
        {step === STEPS.REVIEW && parsedData && (
          <>
            <div style={styles.card}>
              <h2 style={styles.sectionTitle}>
                Review & Edit
                {warnings.length > 0 && (
                  <span style={styles.warningBadge}>⚠️ {warnings.length} warning{warnings.length > 1 ? 's' : ''}</span>
                )}
              </h2>
              <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
                Check the data below — click any score to correct it before submitting to Google Sheets.
              </p>
              <ScorecardTable
                data={parsedData}
                onChange={setParsedData}
              />

              <SubmitPanel
                onSubmit={handleSubmit}
                onReset={handleReset}
                overwrite={overwrite}
                onOverwriteChange={setOverwrite}
                error={error}
              />
            </div>
          </>
        )}

        {/* SUBMITTING */}
        {step === STEPS.SUBMITTING && (
          <div style={{ ...styles.card, textAlign: 'center', padding: 48 }}>
            <span style={styles.spinner} />
            <span style={{ fontSize: 16, color: 'var(--mid)' }}>Writing to Google Sheets...</span>
          </div>
        )}

        {/* SUCCESS */}
        {step === STEPS.SUCCESS && result && (
          <div style={styles.card}>
            <div style={styles.success}>
              <p style={styles.successTitle}>🎉 Round Saved!</p>
              <p style={{ fontSize: 15, color: '#2e7d32', marginBottom: 16 }}>
                {result.rows_written} player row{result.rows_written !== 1 ? 's' : ''} written to Google Sheets
                {result.rows_skipped > 0 && ` · ${result.rows_skipped} skipped (already exist)`}
              </p>
              {result.sheet_url && (
                <a
                  href={result.sheet_url}
                  target="_blank"
                  rel="noreferrer"
                  style={styles.successLink}
                >
                  Open Google Sheet →
                </a>
              )}
              {result.warnings?.length > 0 && (
                <div style={{ marginTop: 12, fontSize: 12, color: '#7c5a00' }}>
                  {result.warnings.map((w, i) => <div key={i}>⚠️ {w}</div>)}
                </div>
              )}
            </div>

            <div style={{ marginTop: 20, textAlign: 'center' }}>
              <button style={styles.parseBtn} onClick={handleReset}>
                + Add Another Round
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
